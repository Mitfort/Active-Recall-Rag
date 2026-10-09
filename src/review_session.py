from src.database import (
    get_daily_review_concepts,
    get_learning_state,
    save_review
)

from src.retrieval import semantic_search

from src.context import build_context

from src.generator import generate_question

from src.scheduler import calculate_next_review


def run_daily_review(embedding_model, limit:int = 10):
    concepts = get_daily_review_concepts(limit=limit)

    if not concepts:
        print("Nothing to review today.")
        return

    print("\n" + "=" * 30 + "\n")
    print("DAILTY ACTIVE RECALL")
    print("\n" + "=" * 30 + "\n")

    for index, concept in enumerate(concepts,start=1):

        print(
            f"{index}. {concept['heading']} [{concept['note']}]"
        )

    input("\nPress Enter to start the review session...")

    # REVIEW SESSION one by one 

    for index, concept in enumerate(concepts,start=1):
        print("\n" + "=" * 30 )

        print(
            f"QUESTION "
            f"{index}/{len(concepts)}"
        )

        print(
            f"\nTarget Concept: {concept['heading']}"
        )

        # Retrival

        query = concept['heading'] + "\n" + concept['content']

        retrieval_results = semantic_search(
            query=query,
            embedding_model=embedding_model,
            top_k=3
        )

        # Build context
        context = build_context(retrieval_results)

        # Generate question
        topic = (
            "The main concept to test is: "
            f"{concept['heading']}. "
            "Generate a question primarily focused on this concept, but you can also include related concepts. "
        )

        question = generate_question(
            context=context,
            topic=topic
        )

        # Show question 
        print("\n")

        print(question.question)

        # User anwer
        user_answer = input("\nYour answer: \n")

        # Expected answer 

        print("\nExpected answer: \n")
        print(question.expected_answer)

        # Feedback

        print("""
        How well did you know it? 
        1 - Again
        2 - Hard
        3 - Good 
        4 - Easy
        5 - Perfect
        """)

        while True:
            try:
                user_feedback = int(input("Your feedback (1-5): "))
                if user_feedback < 1 or user_feedback > 5:
                    raise ValueError
                break
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 5.")

        # Update learning state
        concept_id = concept['id']

        state = get_learning_state(concept_id)

        new_mastery, next_review = calculate_next_review(
            rating=user_feedback,
            current_mastery=state['mastery']
        )

        save_review(
            concept_id=concept_id,
            question=question.question,
            expected_answer=question.expected_answer,
            user_answer=user_answer,
            rating=user_feedback,
            new_mastery=new_mastery,
            next_review=next_review
        )

        print(
            f"\nMastery:"
            f"{state['mastery']:.0%}"
            f" -> "
            f"{new_mastery:.0%}"
        )

        print(
            f"Next review: "
            f"{next_review.date()}"
        )

    print("\n" + "=" * 30 + "\n")

    print("REVIEW SESSION COMPLETED")

    