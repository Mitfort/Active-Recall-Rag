from src.ingestion import load_notes, NoteChunk, ParsedNote

from src.database import initialize_database, sync_note, get_all_concepts

def main():
    initialize_database()

    notes: list[ParsedNote] = load_notes("data/notes")
    print(f"Loaded {len(notes)} notes from the directory.")
    print(f"Synchronizing notes...\\n")

    for note in notes:
        print("=" * 60)

        status = sync_note(note)
        print(f"File: {note.file_name} - Status: {status}")

    print("=" * 60)
    print(f"\\nConcepts in database:")
    concepts = get_all_concepts()

    for concept in concepts: 
        print("=" * 30)

        print(f"ID: {concept['id']}")
        print(f"Note: {concept['note_title']}")
        print(f"Concept: {concept['heading']}")

        print()

        print(concept['content'])

        print()

if __name__ == "__main__":
    main()