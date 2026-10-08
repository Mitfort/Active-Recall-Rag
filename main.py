from src.ingestion import load_notes, NoteChunk, ParsedNote

from src.database import initialize_database, sync_note, get_all_concepts

from src.embeddings import (
    EmbeddingModel,
    generate_missing_embeddings
)

from src.retrieval import semantic_search

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

    embedding_model = EmbeddingModel()

    generate_missing_embeddings(embedding_model)

    while True:
        print()

        query = input(
            "Search your knowledge base"
            "(or type 'exit' to quit): "
        )

        if query.lower() == 'exit':
            break

        results = semantic_search(
            query=query,
            embedding_model=embedding_model,
            top_k=3
        )

        print("\nResults:\\n")

        for index, result in enumerate(results, start=1):
            print(
                f"{index}."
                f"{result['heading']}"
            )

            print(f"Note: {result['note']}")

            print(
                f"Similarity: "
                f"{result['score']:.4f}"
            )

            print()

            print(result['content'])

if __name__ == "__main__":
    main()