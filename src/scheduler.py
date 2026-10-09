from datetime import datetime, timedelta 

def calculate_next_review(
        rating:int,
        current_mastery: float
) -> tuple[float,datetime]:
    """
    Calculate the next review date based on the rating and current mastery level.

    Args:
        rating (int): The rating given by the user (1-5).
        current_mastery (float): The current mastery level of the item (0.0-1.0).

    Returns:
        tuple[float, datetime]: A tuple containing the new mastery level and the next review date.
    """

    # RATINGS
    # 1 = "Again"
    # 2 = "Hard"
    # 3 = "Good"
    # 4 = "Easy"
    # 5 = "Perfect"

    if rating == 1:
        mastery_change = -0.15
        interval_days = 1

    elif rating == 2:
        mastery_change = 0.05
        interval_days = 2

    elif rating == 3:
        mastery_change = 0.12
        interval_days = 4

    elif rating == 4:
        mastery_change = 0.20
        interval_days = 7

    elif rating == 5:
        mastery_change = 0.30
        interval_days = 14

    else:
        raise ValueError(
            "Rating must be between 1 and 5."
        )

    # Update mastery level
    new_mastery = current_mastery + mastery_change

    new_mastery = max(
        0.0, 
        min(new_mastery, 1.0)
    )

    # The more mastered the item is
    # the longer the interval 

    mastery_multiplier = 1 + 2 * new_mastery

    interval_days = round(interval_days * mastery_multiplier)

    next_review = datetime.now() + timedelta(days=interval_days)

    return new_mastery, next_review

def calculate_learning_score(
        correctness:float,
        confidence:int,
        difficulty:int
) -> tuple[float, int]:
    """
    correctness:
        AI evaluation 0-1

    confidence:
        1 = guessed / very unsure
        2 = unsure
        3 = fairly confident
        4 = very confident
        5 = completely confident

    difficulty:
        question difficulty 1-5

    Returns:
        combined_score
        scheduler_rating
    """

    if confidence < 1 or confidence > 5:
        raise ValueError(
            "Confidence must be between 1 and 5."
        )

    if difficulty < 1 or difficulty > 5:
        raise ValueError(
            "Difficulty must be between 1 and 5."
        )

    confidence_score = (confidence - 1) / 3

    # Harder question gives small bonus
    # difficulty 1 -> -0.08
    # difficulty 3 -> 0
    # difficulty 5 -> +0.08

    difficulty_adjustment = (difficulty - 3) * 0.04

    adjusted_corectness = correctness + difficulty_adjustment

    adjusted_corectness = max(
        0.0,
        min(adjusted_corectness, 1.0)
    )

    # AI has more weight than self-assessment

    combined_score = (
        0.8 * adjusted_corectness + 
        0.2 * confidence_score
    )

    # Confidence cannot save a completly
    # wrong answer 

    if correctness < 0.35:
        rating = 1
    elif combined_score < 0.5:
        rating = 2
    elif combined_score < 0.65:
        rating = 3
    elif combined_score < 0.85:
        rating = 4
    else:
        rating = 5

    return (combined_score, rating)
