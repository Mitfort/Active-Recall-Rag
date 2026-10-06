from src.ingestion import load_notes

def main():
    chunks = load_notes("data/notes")

    print(f"Loaded {len(chunks)} note chunks.\n")

    for chunk in chunks:
        print("=" * 60)

        print(f"File: {chunk.file_name}")
        print(f"Title: {chunk.title}")
        print(f"Concept: {chunk.heading}")

        print()

        print(chunk.content)

        print()


if __name__ == "__main__":
    main()