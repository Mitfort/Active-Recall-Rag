from src.database import (
    get_daily_review_concepts,
    get_learning_state,
    save_review
)

from src.retrieval import semantic_search

from src.context import build_context

from src.generator import generate_question

from src.scheduler import (
    calculate_learning_score,
    update_memory_state
)

from src.evaluator import evaluate_answer


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

        print("\nEvaluating your answer...\n")

        # Evaluate answer
        evaluation = evaluate_answer(
            question=question.question,
            expected_answer=question.expected_answer,
            student_answer=user_answer,
            context=context
        )

        print(
            "\n" + "=" * 30 + "\n"
        )

        print("EVALUATION\n")

        print(
            f"Correctness Score: "
            f"{evaluation.correctness:.0%}"
        )

        print(
            f"Verdict: "
            f"{evaluation.verdict}"
        )

        if evaluation.missing_points:
            print(
                "\nMissing Points:\n")

            for point in evaluation.missing_points:
                print(f"- {point}")

        if evaluation.missconceptions:
            print(
                "\nMisconceptions:\n")

            for misconception in evaluation.missconceptions:
                print(f"- {misconception}")

        print(
            "\nFeedback:\n"
            f"{evaluation.feedback}"
        )

        # Expected answer 

        print("\nExpected answer: \n")
        print(question.expected_answer)

        # Confidence rating
        print(
            """
            How confident were you BEFORE seeing the answer? 
            1 - Guessed / Very unsure
            2 - Unsure
            3 - Fairly confident
            4 - Very confident
            5 - Completely confident
            """
        )

        while True:
            try:
                confidence = int(input("Confidence: "))

                if confidence < 1 or confidence > 5:
                    raise ValueError(
                        "Confidence must be between 1 and 5."
                    )
                break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a number between 1 and 5.")

        combined_score, rating = calculate_learning_score(
            correctness=evaluation.correctness,
            confidence=confidence,
            difficulty=question.dificulty
        )

        # Update learning state
        concept_id = concept['id']

        state = get_learning_state(concept_id)

        new_mastery, new_stability, next_review = update_memory_state(
            current_mastery=state['mastery'],
            current_stability=state['stability_days'],
            combined_score=combined_score
        )

        save_review(
            concept_id=concept_id,
            question=question.question,
            expected_answer=question.expected_answer,
            user_answer=user_answer,
            rating=rating,

            new_mastery=new_mastery,
            new_stability=new_stability,
            next_review=next_review,

            ai_correctness=evaluation.correctness,
            ai_feedback=evaluation.feedback,
            missing_points=evaluation.missing_points,
            misconceptions=evaluation.missconceptions,

            user_confidence=confidence,
            combined_score=combined_score
        )

        print(
            f"\nMastery:"
            f"{state['mastery']:.0%}"
            f" -> "
            f"{new_mastery:.0%}"
        )

        print(
            f"Stability:"
            f"{state['stability_days']} days"
            f" -> "
            f"{new_stability:.0f} days"
        )

        print(
            f"Next review: "
            f"{next_review.date()}"
        )

    print("\n" + "=" * 30 + "\n")

    print("REVIEW SESSION COMPLETED")

