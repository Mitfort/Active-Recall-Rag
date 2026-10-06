from dataclasses import dataclass
from pathlib import Path
import re 

@dataclass
class NoteChunk:
    file_name: str
    title: str
    heading: str
    content: str 

def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding='utf-8')

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

def process_note(path: Path) -> list[NoteChunk]:
    markdown = read_markdown_file(path)
    title = extract_title(markdown)
    sections = split_into_sections(markdown)

    note_chunks = []

    for heading, content in sections:
        note_chunk = NoteChunk(
            file_name=path.name,
            title=title,
            heading=heading,
            content=content
        )
        note_chunks.append(note_chunk)

    return note_chunks

def load_notes(directory: str) -> list[NoteChunk]:
    notes_directory = Path(directory)

    all_chunks = []

    for file_path in notes_directory.rglob("*.md"):
        chunk = process_note(file_path)

        all_chunks.extend(chunk)

    return all_chunks