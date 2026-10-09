from src.ingestion import load_notes, NoteChunk, ParsedNote

from src.database import (
    initialize_database, 
    sync_note, 
    get_learning_state,
    save_review
)

from src.embeddings import (
    EmbeddingModel,
    generate_missing_embeddings
)

from src.retrieval import semantic_search

from src.context import build_context

from src.generator import generate_question

from src.scheduler import calculate_next_review

from src.review_session import run_daily_review


def main():
    initialize_database()

    # =========
    # INGESTION 
    # ========= 

    notes: list[ParsedNote] = load_notes("data/notes")
    print(f"Loaded {len(notes)} notes from the directory.")
    print(f"Synchronizing notes...\\n")

    for note in notes:
        print("=" * 60)

        status = sync_note(note)
        print(f"File: {note.file_name} - Status: {status}")

    print("=" * 60)

    # =========
    # EMBEDDING
    # =========

    embedding_model = EmbeddingModel()

    generate_missing_embeddings(embedding_model)

    # =========
    # Quiz 
    # =========

    while True:
        print()
        print("""
        ========================================

        ACTIVE RECALL

        1 - Daily Review
        2 - Practice a topic
        3 - Exit

        ========================================
        """
        )

        choice = input("Choose: ")

        if choice == "1":
            run_daily_review(embedding_model,limit=10)
        elif choice == "2":
            topic = input(
                "What do you want to practice?"
                "(or type 'exit' to quit): "
            )

            if topic.lower() == 'exit':
                break

            # RETRIEVE

            results = semantic_search(
                query=topic,
                embedding_model=embedding_model,
                top_k=3
            )

            print("\nRetrieved results:\\n")

            for result in results:
                print(
                    f"- [{result['id']}] "
                    f"{result['heading']}"
                    f"({result['score']:.4f})"
                )

            # BUILD CONTEXT

            context = build_context(results)

            # GENERATE QUESTION

            question = generate_question(
                context=context,
                topic=topic
            )

            print(
                "\n"
                + "=" * 60
            )

            print("\nQUESTION\n")

            print(question.question)

            print()

            print("\nEXPECTED ANSWER\n")

            print(question.expected_answer)

        elif choice == "3":
            print("Exiting...")
            break

        # print(
        #     f"Difficulty:"
        #     f"{question.dificulty}/5"
        # )

        # print(
        #     f"Type: "
        #     f"{question.question_type}"
        # )

        # print(
        #     f"Concept IDs: "
        #     f"{question.concept_ids}"
        # )

if __name__ == "__main__":
    main()