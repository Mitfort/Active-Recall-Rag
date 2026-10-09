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

        user_answer = input(
            "Your answer:\n"
        )

        print("\nEXPECTED ANSWER\n")

        print(question.expected_answer)

        print()

        print("""
            How well did you answer the question?
            1 = "Again"
            2 = "Hard"
            3 = "Good"
            4 = "Easy"
            5 = "Very Easy"
            """
        )

        while True:
            try: 
                rating = int(input("Rating (1-5): "))
                if 1 <= rating <= 5:
                    break
                else:
                    print("Please enter a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid number.")

        for concept_id in question.concept_ids:

            state = get_learning_state(concept_id)

            new_mastery, next_review_date = calculate_next_review(
                rating=rating,
                current_mastery=state['mastery']
            )

            save_review(
                concept_id=concept_id,
                question=question.question,
                expected_answer=question.expected_answer,
                user_answer=user_answer,
                rating=rating,
                new_mastery=new_mastery,
                next_review = next_review_date
            )

            print(f"\nConcept {concept_id}")

            print(
                f"Mastery: "
                f"{state['mastery']:.2f} -> "
                f"{new_mastery:.2f}"
            )

            print(
                f"Next Review: "
                f"{next_review_date.date()}"
            )

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