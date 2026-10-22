from dataclasses import dataclass
from pathlib import Path
import hashlib 
import re 
import yaml 

ATTACHMENT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif", ".ico",
    ".pdf", ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".webm",
    ".mov", ".avi", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
    ".pptx", ".csv", ".txt", ".canvas", ".excalidraw",
}

@dataclass
class NoteChunk:
    file_name: str
    file_path: str
    title: str
    heading: str
    content: str
    position: int

@dataclass 
class WikiLink:
    target: str
    heading: str | None
    alias: str | None 

@dataclass
class ParsedNote:
    file_name: str
    file_path: str
    
    title: str
    subject: str

    raw_content: str
    content_hash: str

    metadata: dict

    tags: list[str]
    links: list[WikiLink]

    chunks: list[NoteChunk]

def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding='utf-8')

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_title(markdown: str, fallback: str = "Untitled") -> str:
    match = re.search(r"^# (.+)$", markdown, re.MULTILINE)

    if match:
        return match.group(1).strip()

    return fallback

def split_into_sections(markdown: str) -> list[tuple[str, str]]:
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    matches = list(heading_pattern.finditer(markdown))

    if not matches:
        cleaned = re.sub(r"^---\n.*?\n---\n", "", markdown, flags=re.DOTALL)
        cleaned = re.sub(r"^# .+\n", "", cleaned, count=1)
        cleaned = cleaned.strip()
        return [("Overview", cleaned)] if cleaned else []

    sections = []

    for idx, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()

        if level < 2:
            continue

        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        content = markdown[start:end].strip()

        if content:
            sections.append((heading, content))

    if sections:
        return sections

    title = extract_title(markdown)
    cleaned = re.sub(r"^---\n.*?\n---\n", "", markdown, flags=re.DOTALL)
    cleaned = re.sub(r"^# .+\n", "", cleaned, count=1)
    cleaned = cleaned.strip()

    return [(title, cleaned)] if cleaned else []

def process_note(path: Path, fallback_subject: str) -> ParsedNote:
    raw_markdown = read_markdown_file(path)

    metadata, body = parse_frontmatter(raw_markdown)

    title = extract_title(body, fallback=path.stem)

    subject = metadata.get("subject") or fallback_subject or "General"

    subject = subject.strip()

    tags = extract_tags(metadata, body)

    links = extract_wikilinks(body, current_note_title=title)

    content_hash = calculate_hash(raw_markdown)

    sections = split_into_sections(body)

    chunks = []

    for position, (heading, content) in enumerate(sections):
        chunk = NoteChunk(
            file_name=path.name,
            file_path=str(path),
            title=title,
            heading=heading,
            content=content,
            position=position
        )
        chunks.append(chunk)

    return ParsedNote(
        file_name=path.name,
        file_path=str(path),
        title=title,
        subject=subject,
        raw_content=raw_markdown,
        content_hash=content_hash,
        metadata=metadata,
        tags=tags,
        links=links,
        chunks=chunks
    )


def load_notes(directory: str) -> list[ParsedNote]:
    notes_directory = Path(directory)

    notes = []

    for file_path in notes_directory.rglob("*.md"):

        relative_path = file_path.relative_to(
            notes_directory
        )

        if len(relative_path.parts) > 1:
            fallback_subject = relative_path.parts[0]
        else:
            fallback_subject = "General"

        note = process_note(file_path, fallback_subject=fallback_subject)
        notes.append(note)

    return notes

def parse_frontmatter(
    markdown: str
) -> tuple[dict, str]:
    """
    Returns:
    - metadata: dict
    - markdown body without YAML frontmatter
    """

    if not markdown.startswith("---"):
        return {}, markdown

    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n?(.*)$",
        markdown,
        re.DOTALL,
    )

    if not match: 
        return {}, markdown

    yaml_content = match.group(1)

    body = match.group(2)

    try:
        metadata = yaml.safe_load(yaml_content) or {}

    except yaml.YAMLError:
        metadata = {}

    if not isinstance(metadata, dict):
        metadata = {}

    return metadata, body

def extract_tags(
    metadata: dict,
    markdown_body: str
) -> list[str]:

    tags = set()


    ### FRONTMATTER TAGS 

    metadata_tags = metadata.get("tags", [])

    if isinstance(metadata_tags, str):
        metadata_tags = [metadata_tags]

    if isinstance(metadata_tags, list):
        for tag in metadata_tags:
            if isinstance(tag, str):
                normalized = tag.strip().lstrip("#")

                if normalized:
                    tags.add(normalized)


    ### INLINE TAGS

    inline_tags = re.findall(
        r"(?<!\w)#([A-Za-z0-9_\-/]+)",
        markdown_body,
    )

    for tag in inline_tags:
        normalized = tag.strip().lstrip("#")

        if normalized:
            tags.add(normalized)

    return sorted(tags)

def extract_wikilinks(
    markdown_body: str,
    *,
    current_note_title: str | None = None,
) -> list[WikiLink]:

    raw_links = re.findall(
        r"\[\[([^\]]+)\]\]",
        _strip_link_examples(markdown_body),
    )

    links: list[WikiLink] = []

    for raw_link in raw_links:
        alias = None 
        heading = None 

        target_part = raw_link

        ## [[Target|Alias]]

        if "|" in target_part:
            target_part, alias = target_part.split("|", 1)
            alias = alias.strip() or None

        ## [[Target#Heading]]

        if "#" in target_part:
            target_part, heading = target_part.split("#", 1)
            heading = heading.strip() or None

        target = target_part.strip()
        if not target and heading and current_note_title:
            target = current_note_title

        if not target or Path(target).suffix.lower() in ATTACHMENT_EXTENSIONS:
            continue

        links.append(
            WikiLink(
                target=target,
                heading=heading,
                alias=alias
            )
        )

    return links


def _strip_link_examples(markdown: str) -> str:
    """Remove code and hidden comments before extracting note references."""
    visible_lines = []
    fence_character = None
    fence_length = 0

    for line in markdown.splitlines(keepends=True):
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence_character is not None:
            if (
                fence
                and fence.group(1)[0] == fence_character
                and len(fence.group(1)) >= fence_length
                and not line[fence.end():].strip()
            ):
                fence_character = None
            continue

        if fence:
            fence_character = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue

        visible_lines.append(line)

    visible = "".join(visible_lines)
    visible = re.sub(r"<!--.*?(?:-->|$)|%%.*?(?:%%|$)", "", visible, flags=re.DOTALL)
    return re.sub(r"(`+).*?\1", "", visible, flags=re.DOTALL)
