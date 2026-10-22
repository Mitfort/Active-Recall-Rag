"""Build the knowledge hierarchy from indexed folders, tags and note sections."""

import json
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath

from src.ingestion import ATTACHMENT_EXTENSIONS
from src.scheduler import calculate_retrievability

NOTES_ROOT = Path(__file__).resolve().parent.parent / "data" / "notes"


def build_knowledge_graph(
    notes: list[dict],
    links: list[dict],
    knowledge_rows: list[dict],
    notes_root: Path | str = NOTES_ROOT,
) -> dict:
    """Return folder → topic → note → concept edges and related-topic links."""
    if not notes:
        return {"nodes": [], "edges": [], "unresolved_links": []}

    nodes: dict[int | str, dict] = {}
    edges = []
    edge_keys = set()
    folders = {}
    branch_paths = {}
    note_folders = {}
    note_concepts = defaultdict(list)
    aliases = defaultdict(set)
    exact_aliases = defaultdict(set)
    concept_aliases = defaultdict(lambda: defaultdict(set))

    def add_edge(source: int | str, target: int | str, kind: str) -> None:
        key = (source, target, kind)
        if source != target and key not in edge_keys:
            edges.append({"source": source, "target": target, "type": kind, "score": None})
            edge_keys.add(key)

    def register_alias(label: str, node_id: int | str) -> None:
        key = _link_key(label)
        if key:
            aliases[key].add(node_id)
            exact_aliases[_exact_link_key(label)].add(node_id)

    def add_branch(parts: tuple[str, ...], kind: str) -> int | str:
        # Directory identity must preserve punctuation (C++ and C# differ).
        key = tuple(part.casefold() for part in parts)
        if key in folders:
            return folders[key]
        parent = add_branch(parts[:-1], kind) if parts else None
        node_id = f"{kind}:{'/'.join(key)}"
        nodes[node_id] = _node(
            node_id=node_id, label=parts[-1] if parts else "Notes",
            subject="/".join(parts), kind=kind, depth=len(parts),
        )
        folders[key] = node_id
        branch_paths[node_id] = parts
        if parent is not None:
            add_edge(parent, node_id, "hierarchy")
            register_alias(parts[-1], node_id)
            register_alias("/".join(parts), node_id)
        return node_id

    # Establish all real folders before adding tag topics, so folders always win.
    for note in notes:
        parts = _folder_parts(note["file_path"], Path(notes_root))
        note_folders[note["id"]] = parts
        add_branch(parts, "domain")

    for row in knowledge_rows:
        note_concepts[row["note_id"]].append(row)

    for note in notes:
        note_id = note["id"]
        parts = note_folders[note_id]
        metadata = json.loads(note["metadata_json"] or "{}")
        parent_ids = set()
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tag_paths = []
        for tag in tags if isinstance(tags, list) else []:
            if not isinstance(tag, str) or "/" not in tag:
                continue
            tag_parts = tuple(part.strip() for part in tag.strip("#/").split("/") if part.strip())
            # The first tag component commonly repeats the top-level folder.
            shared = 0
            while shared < min(len(parts), len(tag_parts)) and _link_key(parts[shared]) == _link_key(tag_parts[shared]):
                shared += 1
            path = parts + tag_parts[shared:]
            if path != parts:
                tag_paths.append(path)
        for path in tag_paths:
            if not any(other != path and other[:len(path)] == path for other in tag_paths):
                parent_ids.add(add_branch(path, "topic"))
        if not parent_ids:
            parent_ids.add(add_branch(parts, "domain"))

        concepts = note_concepts[note_id]
        node = _node(
            node_id=note_id, label=note["title"], subject=note["subject"],
            kind="note", depth=1 + max(nodes[parent]["depth"] for parent in parent_ids),
            note_id=note_id,
        )
        nodes[note_id] = node
        for parent in sorted(parent_ids):
            add_edge(parent, note_id, "hierarchy")
        register_alias(note["title"], note_id)
        file_path = PurePosixPath(note["file_path"].replace("\\", "/"))
        register_alias(file_path.stem, note_id)
        register_alias("/".join((*parts, file_path.stem)), note_id)
        note_aliases = metadata.get("aliases", [])
        if isinstance(note_aliases, str):
            note_aliases = [note_aliases]
        for alias in note_aliases if isinstance(note_aliases, list) else []:
            if isinstance(alias, str):
                register_alias(alias, note_id)

        for concept in concepts:
            concept_id = f"concept:{concept['id']}"
            label = _concept_label(concept, note["title"])
            concept_node = _node(
                node_id=concept_id, label=label, subject=note["title"], kind="concept",
                depth=node["depth"] + 1, note_id=note_id,
            )
            concept_node.update(
                mastery=concept["mastery"],
                retrievability=calculate_retrievability(
                    last_review=concept["last_reviewed"], stability_days=concept["stability_days"],
                ),
                concept_count=1, reviewed_count=int(concept["review_count"] > 0),
            )
            nodes[concept_id] = concept_node
            add_edge(note_id, concept_id, "hierarchy")
            for alias in (concept["heading"], label, _clean_heading(concept["heading"])):
                concept_aliases[note_id][_link_key(alias)].add(concept_id)
        if concepts:
            child_nodes = [nodes[f"concept:{concept['id']}"] for concept in concepts]
            node.update(
                mastery=sum(child["mastery"] for child in child_nodes) / len(concepts),
                retrievability=sum(child["retrievability"] for child in child_nodes) / len(concepts),
                concept_count=len(concepts),
                reviewed_count=sum(child["reviewed_count"] for child in child_nodes),
            )

    unresolved = []
    missing_keys = set()
    for link in links:
        source = link["source_note_id"]
        if source not in nodes:
            continue
        title = link["target_title"]
        if PurePosixPath(title.lower()).suffix in ATTACHMENT_EXTENSIONS:
            continue
        candidates = exact_aliases.get(_exact_link_key(title)) or aliases.get(_link_key(title), set())
        # Prefer real notes; duplicate basenames only resolve in the source folder.
        note_candidates = {candidate for candidate in candidates if nodes[candidate]["type"] == "note"}
        if note_candidates:
            candidates = note_candidates
            local = {candidate for candidate in candidates if note_folders[candidate] == note_folders[source]}
            if len(local) == 1:
                candidates = local
        elif len(candidates) > 1:
            # Repeated topic names resolve in the closest source domain.
            source_parts = note_folders[source]
            proximity = {}
            for candidate in candidates:
                shared = 0
                for left, right in zip(source_parts, branch_paths[candidate]):
                    if left.casefold() != right.casefold():
                        break
                    shared += 1
                proximity[candidate] = shared
            closest = max(proximity.values())
            if closest:
                candidates = {candidate for candidate in candidates if proximity[candidate] == closest}
        target = next(iter(candidates)) if len(candidates) == 1 else None
        heading = link.get("target_heading")
        if target is not None and heading and nodes[target]["type"] == "note":
            matches = concept_aliases[target].get(_link_key(heading), set())
            target = next(iter(matches)) if len(matches) == 1 else None
        if target is None:
            target_title = f"{title}#{heading}" if heading else title
            key = (source, target_title)
            if key not in missing_keys:
                unresolved.append({"source": source, "target_title": target_title})
                missing_keys.add(key)
        else:
            add_edge(source, target, "wikilink")

    return {"nodes": list(nodes.values()), "edges": edges, "unresolved_links": unresolved}


def _node(*, node_id: int | str, label: str, subject: str, kind: str, depth: int, note_id: int | None = None) -> dict:
    return {
        "id": node_id, "label": label, "subject": subject, "type": kind,
        "note_id": note_id, "depth": depth, "mastery": 0.0, "retrievability": 0.0,
        "concept_count": 0, "reviewed_count": 0,
    }


def _folder_parts(file_path: str, notes_root: Path) -> tuple[str, ...]:
    path = Path(file_path.replace("\\", "/"))
    try:
        return path.resolve().relative_to(notes_root.resolve()).parts[:-1]
    except ValueError:
        # Indexed paths can be relative or belong to another machine/checkout.
        normalized = "/" + file_path.replace("\\", "/").lstrip("/")
        marker = "/data/notes/"
        start = normalized.lower().rfind(marker)
        if start >= 0:
            return tuple(normalized[start + len(marker):].split("/")[:-1])
        return ()


def _link_key(value: str) -> str:
    parts = _exact_link_key(value).split("/")
    return "/".join(re.sub(r"[\W_]+", "", _clean_heading(part).casefold()) for part in parts)


def _exact_link_key(value: str) -> str:
    return value.strip().replace("\\", "/").casefold().removesuffix(".md")


def _clean_heading(heading: str) -> str:
    return re.sub(r"^(?:\d+(?:\.\d+)*[.)]?\s+)", "", heading.strip().lstrip("| ")).strip()


def _concept_label(concept: dict, note_title: str) -> str:
    marker = re.search(r"%%\s*Zagadnienie::\s*(.*?)\s*%%", concept["content"], re.DOTALL)
    label = marker.group(1).strip() if marker else _clean_heading(concept["heading"])
    title, separator, detail = label.partition(" — ")
    return detail.strip() if separator and _link_key(title) == _link_key(note_title) else label
