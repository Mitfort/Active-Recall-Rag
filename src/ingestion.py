from dataclasses import dataclass
from pathlib import Path
import hashlib 
import re 

@dataclass
class NoteChunk:
    file_name: str
    file_path: str
    title: str
    heading: str
    content: str
    position: int

@dataclass
class ParsedNote:
    file_name: str
    file_path: str
    title: str
    raw_content: str
    content_hash: str
    chunks: list[NoteChunk]

def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding='utf-8')

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_title(markdown:str) -> str:
    match = re.search(r"^# (.+)$", markdown, re.MULTILINE)

    if match:
        return match.group(1).strip()

    return "Untitled"

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

def process_note(path: Path) -> ParsedNote:
    markdown = read_markdown_file(path)
    title = extract_title(markdown)
    sections = split_into_sections(markdown)

    content_hash = calculate_hash(markdown)

    note_chunks = []

    for position, (heading, content) in enumerate(sections):
        note_chunk = NoteChunk(
            file_name=path.name,
            file_path=str(path),
            title=title,
            heading=heading,
            content=content,
            position=position
        )
        note_chunks.append(note_chunk)

    return ParsedNote(
        file_name=path.name,
        file_path=str(path),
        title=title,
        raw_content=markdown,
        content_hash=content_hash,
        chunks=note_chunks
    )

def load_notes(directory: str) -> list[ParsedNote]:
    notes_directory = Path(directory)

    notes = []

    for file_path in notes_directory.rglob("*.md"):
        note = process_note(file_path)

        notes.append(note)

    return notes