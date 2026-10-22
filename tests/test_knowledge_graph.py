"""Behavioral coverage for the note hierarchy and explicit graph links."""

import json
import re
import unittest
from pathlib import Path

from src.knowledge_graph import build_knowledge_graph


NOTES_ROOT = Path("data/notes")


def note_row(
    note_id: int,
    title: str,
    relative_path: str,
    *,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
) -> dict:
    return {
        "id": note_id,
        "title": title,
        "subject": "MachineLearning",
        "file_path": str(NOTES_ROOT / relative_path),
        "metadata_json": json.dumps({"tags": tags or [], "aliases": aliases or []}),
    }


def concept_row(
    concept_id: int,
    note_id: int,
    heading: str,
    *,
    content: str = "",
    mastery: float = 0.0,
    review_count: int = 0,
    last_reviewed: str | None = None,
) -> dict:
    return {
        "id": concept_id,
        "note_id": note_id,
        "note": "Basis of Decision Trees",
        "subject": "MachineLearning",
        "heading": heading,
        "content": content,
        "mastery": mastery,
        "stability_days": 10.0,
        "review_count": review_count,
        "last_reviewed": last_reviewed,
        "next_review": None,
    }


def link_row(source_note_id: int, title: str, heading: str | None = None) -> dict:
    return {
        "source_note_id": source_note_id,
        "target_title": title,
        "target_heading": heading,
    }


def normalized_label(label: str) -> str:
    return re.sub(r"[^\w]", "", label).casefold()


class KnowledgeGraphTests(unittest.TestCase):
    def build(self, notes: list[dict], links: list[dict] | None = None, concepts: list[dict] | None = None) -> dict:
        return build_knowledge_graph(notes, links or [], concepts or [], notes_root=NOTES_ROOT)

    def node(self, graph: dict, label: str, node_type: str) -> dict:
        matches = [
            node for node in graph["nodes"]
            if node["type"] == node_type
            and normalized_label(node["label"]) == normalized_label(label)
        ]
        self.assertEqual(len(matches), 1, f"Expected one {node_type} node named {label!r}: {matches}")
        return matches[0]

    def assert_connected(self, graph: dict, source: dict, target: dict) -> None:
        self.assertTrue(
            any(edge["source"] == source["id"] and edge["target"] == target["id"] for edge in graph["edges"]),
            f"Missing directed connection: {source['label']} -> {target['label']}",
        )

    def test_empty_index_returns_an_empty_graph(self) -> None:
        self.assertEqual(self.build([]), {"nodes": [], "edges": [], "unresolved_links": []})

    def test_every_parent_folder_forms_a_domain_chain(self) -> None:
        graph = self.build([note_row(1, "Decision Trees", "MachineLearning/Supervised/Trees.md")])

        root = self.node(graph, "Notes", "domain")
        machine_learning = self.node(graph, "MachineLearning", "domain")
        supervised = self.node(graph, "Supervised", "domain")
        note = self.node(graph, "Decision Trees", "note")
        for parent, child in zip([root, machine_learning, supervised], [machine_learning, supervised, note]):
            self.assert_connected(graph, parent, child)
            self.assertEqual(child["depth"], parent["depth"] + 1)

    def test_same_named_nested_folders_keep_separate_parents(self) -> None:
        graph = self.build([
            note_row(1, "Tree Methods", "MachineLearning/Methods/Trees.md"),
            note_row(2, "Statistical Methods", "Statistics/Methods/Inference.md"),
        ])

        methods = [node for node in graph["nodes"] if node["type"] == "domain" and node["label"] == "Methods"]
        self.assertEqual(len(methods), 2)
        self.assertNotEqual(methods[0]["id"], methods[1]["id"])
        for parent_label, note_label in [("MachineLearning", "Tree Methods"), ("Statistics", "Statistical Methods")]:
            parent = self.node(graph, parent_label, "domain")
            note = self.node(graph, note_label, "note")
            child_ids = {edge["target"] for edge in graph["edges"] if edge["source"] == parent["id"]}
            children = [node for node in methods if node["id"] in child_ids]
            self.assertEqual(len(children), 1)
            self.assert_connected(graph, children[0], note)

    def test_folder_names_with_distinct_punctuation_keep_separate_branches(self) -> None:
        graph = self.build([
            note_row(1, "Pointers", "Programming/C++/Memory.md"),
            note_row(2, "Managed Memory", "Programming/C#/Memory.md"),
        ])

        cpp = next(node for node in graph["nodes"] if node["type"] == "domain" and node["label"] == "C++")
        csharp = next(node for node in graph["nodes"] if node["type"] == "domain" and node["label"] == "C#")
        self.assertNotEqual(cpp["id"], csharp["id"])
        self.assert_connected(graph, cpp, self.node(graph, "Pointers", "note"))
        self.assert_connected(graph, csharp, self.node(graph, "Managed Memory", "note"))
        hierarchy = {(edge["source"], edge["target"]) for edge in graph["edges"] if edge["type"] == "hierarchy"}
        self.assertNotIn((cpp["id"], 2), hierarchy)
        self.assertNotIn((csharp["id"], 1), hierarchy)

    def test_real_note_tags_reuse_folder_and_create_related_topics(self) -> None:
        graph = self.build([
            note_row(1, "Basis of Decision Trees", "MachineLearning/8.1 Basis of Decision Trees.md", tags=["machineLearning", "machineLearning/treeBasedMethods"]),
            note_row(2, "Ordinary Least Squares", "MachineLearning/OLS.md", tags=["machineLearning/linearRegression"]),
        ], [link_row(1, "8. Tree-Based Methods"), link_row(1, "Linear Regression")])

        machine_learning = self.node(graph, "MachineLearning", "domain")
        tree_methods = self.node(graph, "treeBasedMethods", "topic")
        linear_regression = self.node(graph, "linearRegression", "topic")
        tree_note = self.node(graph, "Basis of Decision Trees", "note")
        regression_note = self.node(graph, "Ordinary Least Squares", "note")
        self.assert_connected(graph, machine_learning, tree_methods)
        self.assert_connected(graph, machine_learning, linear_regression)
        self.assert_connected(graph, tree_methods, tree_note)
        self.assert_connected(graph, linear_regression, regression_note)
        self.assert_connected(graph, tree_note, linear_regression)
        self.assertFalse(graph["unresolved_links"])
        self.assertEqual(sum(normalized_label(node["label"]) == "machinelearning" for node in graph["nodes"]), 1)

    def test_explicit_concept_markers_supply_labels_and_fallback_cleans_heading(self) -> None:
        graph = self.build(
            [note_row(1, "Basis of Decision Trees", "MachineLearning/Trees.md")],
            concepts=[
                concept_row(10, 1, "| 8.1.1 Regression Trees", content="%% Zagadnienie:: Basis of Decision Trees — Regression Trees %%\n\nExplanation."),
                concept_row(11, 1, "| 8.1.2 Classification Trees"),
            ],
        )

        note = self.node(graph, "Basis of Decision Trees", "note")
        for label in ["Regression Trees", "Classification Trees"]:
            concept = self.node(graph, label, "concept")
            self.assertEqual(concept["note_id"], 1)
            self.assertEqual(concept["depth"], note["depth"] + 1)
            self.assert_connected(graph, note, concept)

    def test_repeated_topic_name_resolves_in_the_source_domain(self) -> None:
        graph = self.build([
            note_row(1, "Overview", "MachineLearning/Overview.md"),
            note_row(2, "Prediction", "MachineLearning/Prediction.md", tags=["machineLearning/linearRegression"]),
            note_row(3, "Inference", "Statistics/Inference.md", tags=["statistics/linearRegression"]),
        ], [link_row(1, "Linear Regression")])

        machine_learning = self.node(graph, "MachineLearning", "domain")
        topics = [node for node in graph["nodes"] if node["type"] == "topic" and node["label"] == "linearRegression"]
        self.assertEqual(len(topics), 2)
        local_topic_ids = {
            edge["target"] for edge in graph["edges"]
            if edge["source"] == machine_learning["id"] and edge["type"] == "hierarchy"
        }
        local_topic = next(node for node in topics if node["id"] in local_topic_ids)
        links = {(edge["source"], edge["target"]) for edge in graph["edges"] if edge["type"] == "wikilink"}
        self.assertEqual(links, {(1, local_topic["id"])})
        self.assertFalse(graph["unresolved_links"])

    def test_wikilinks_resolve_titles_stems_paths_and_aliases(self) -> None:
        notes = [
            note_row(1, "Overview", "Overview.md"),
            note_row(2, "Basis of Decision Trees", "MachineLearning/8.1 Basis of Decision Trees.md", aliases=["Decision Tree Primer"]),
        ]
        for target in [
            "BASIS OF DECISION TREES",
            "8.1 Basis of Decision Trees",
            "MachineLearning/8.1 Basis of Decision Trees",
            "MachineLearning/8.1 Basis of Decision Trees.md",
            "MACHINELEARNING/8.1 BASIS OF DECISION TREES.MD",
            "decision tree primer",
        ]:
            with self.subTest(target=target):
                graph = self.build(notes, [link_row(1, target)])
                self.assert_connected(graph, self.node(graph, "Overview", "note"), self.node(graph, "Basis of Decision Trees", "note"))
                self.assertFalse(graph["unresolved_links"])

    def test_duplicate_note_titles_resolve_locally_or_by_full_path(self) -> None:
        notes = [
            note_row(1, "Overview", "MachineLearning/Overview.md"),
            note_row(2, "Shared Topic", "MachineLearning/Shared.md"),
            note_row(3, "Shared Topic", "Statistics/Shared.md"),
        ]
        graph = self.build(notes, [link_row(1, "Shared Topic"), link_row(1, "Statistics/Shared")])

        self.assertIn((1, 2), {(edge["source"], edge["target"]) for edge in graph["edges"]})
        self.assertIn((1, 3), {(edge["source"], edge["target"]) for edge in graph["edges"]})
        self.assertFalse(graph["unresolved_links"])

    def test_ambiguous_nonlocal_note_titles_stay_unresolved(self) -> None:
        graph = self.build(
            [
                note_row(1, "Overview", "Overview.md"),
                note_row(2, "Shared Topic", "MachineLearning/Shared.md"),
                note_row(3, "Shared Topic", "Statistics/Shared.md"),
            ],
            [link_row(1, "Shared Topic")],
        )

        self.assertEqual(len(graph["unresolved_links"]), 1)
        self.assertFalse(any(edge["source"] == 1 and edge["type"] == "wikilink" for edge in graph["edges"]))

    def test_heading_link_targets_the_matching_concept(self) -> None:
        graph = self.build(
            [note_row(1, "Overview", "Overview.md"), note_row(2, "Basis of Decision Trees", "MachineLearning/Trees.md")],
            [link_row(1, "Basis of Decision Trees", "8.1.1 Regression Trees")],
            [concept_row(10, 2, "| 8.1.1 Regression Trees", content="%% Zagadnienie:: Basis of Decision Trees — Regression Trees %%")],
        )

        self.assert_connected(graph, self.node(graph, "Overview", "note"), self.node(graph, "Regression Trees", "concept"))
        self.assertFalse(graph["unresolved_links"])

    def test_persisted_attachment_links_do_not_pollute_graph(self) -> None:
        graph = self.build(
            [note_row(1, "Overview", "Overview.md")],
            [link_row(1, target) for target in ["Pasted image 20251127083831.png", "diagram.JPG", "figure.svg", "reference.pdf", "lecture.m4a"]],
        )

        self.assertFalse(graph["unresolved_links"])
        self.assertEqual([node["label"] for node in graph["nodes"] if node["type"] == "note"], ["Overview"])

    def test_exact_folder_link_preserves_meaningful_punctuation(self) -> None:
        graph = self.build(
            [note_row(1, "Pointers", "Programming/C++/Pointers.md"),
             note_row(2, "Classes", "Programming/C#/Classes.md")],
            [link_row(1, "C#")],
        )
        target = next(node for node in graph["nodes"] if node["type"] == "domain" and node["label"] == "C#")
        self.assertIn((1, target["id"]), {(edge["source"], edge["target"]) for edge in graph["edges"] if edge["type"] == "wikilink"})
        self.assertFalse(graph["unresolved_links"])

    def test_duplicate_links_and_selflinks_do_not_duplicate_graph_edges(self) -> None:
        graph = self.build(
            [note_row(1, "Overview", "Overview.md"), note_row(2, "Trees", "MachineLearning/Trees.md")],
            [link_row(1, "Trees"), link_row(1, "Trees"), link_row(1, "Overview"), link_row(1, "Missing"), link_row(1, "Missing")],
        )

        edges = [(edge["source"], edge["target"], edge.get("type")) for edge in graph["edges"]]
        self.assertEqual(len(edges), len(set(edges)))
        self.assertTrue(all(source != target for source, target, _ in edges))
        self.assertEqual(len(graph["unresolved_links"]), 1)
        self.assert_connected(graph, self.node(graph, "Overview", "note"), self.node(graph, "Trees", "note"))

    def test_crosslink_cycles_leave_hierarchical_depth_unchanged(self) -> None:
        notes = [
            note_row(1, "Overview", "Overview.md"),
            note_row(2, "Deep Topic", "MachineLearning/Methods/Deep.md"),
        ]
        before = self.build(notes)
        after = self.build(notes, [link_row(1, "Deep Topic"), link_row(2, "Overview")])

        self.assertEqual({node["id"]: node["depth"] for node in before["nodes"]}, {node["id"]: node["depth"] for node in after["nodes"]})
        self.assert_connected(after, self.node(after, "Overview", "note"), self.node(after, "Deep Topic", "note"))
        self.assert_connected(after, self.node(after, "Deep Topic", "note"), self.node(after, "Overview", "note"))

    def test_note_metrics_aggregate_concepts_including_unreviewed(self) -> None:
        graph = self.build(
            [note_row(1, "Basis of Decision Trees", "MachineLearning/Trees.md")],
            concepts=[
                concept_row(10, 1, "Regression Trees", mastery=0.9, review_count=2, last_reviewed="2999-01-01T00:00:00"),
                concept_row(11, 1, "Classification Trees", mastery=0.3),
            ],
        )

        note = self.node(graph, "Basis of Decision Trees", "note")
        self.assertEqual(note["concept_count"], 2)
        self.assertEqual(note["reviewed_count"], 1)
        self.assertAlmostEqual(note["mastery"], 0.6)
        self.assertAlmostEqual(note["retrievability"], 0.5)
        self.assertEqual(self.node(graph, "Regression Trees", "concept")["reviewed_count"], 1)
        self.assertEqual(self.node(graph, "Classification Trees", "concept")["retrievability"], 0.0)

    def test_root_level_note_is_attached_to_notes_root(self) -> None:
        graph = self.build([note_row(1, "Overview", "Overview.md")])

        root = self.node(graph, "Notes", "domain")
        note = self.node(graph, "Overview", "note")
        self.assert_connected(graph, root, note)
        self.assertEqual(root["depth"], 0)
        self.assertEqual(note["depth"], 1)


if __name__ == "__main__":
    unittest.main()
