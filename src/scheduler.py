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