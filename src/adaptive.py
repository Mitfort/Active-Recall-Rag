from dataclasses import dataclass
import json 

from src.scheduler import calculate_retrievability

@dataclass
class ReviewStrategy:
    question_type: str
    difficulty: str

    focus: str
    reason: str

def parse_json_list(
    value: str | None
) -> list[str]:

    if not value:
        return []

    try:
        data = json.loads(value)

        if isinstance(data, list):
            return data

    except json.JSONDecodeError:
        return []

    return []

def choose_review_strategy(
    state: dict,
    recent_reviews: list[dict]
) -> ReviewStrategy:

    mastery = float(state['mastery'])

    retrievability = calculate_retrievability(
        last_review=state['last_reviewed'],
        stability_days=state['stability_days']
    )

    recent_misconceptions = []
    recent_missing_points = []

    # Analyze a few recent reviews to determine the focus and reason for the next review

    for review in recent_reviews[:3]:

        misconceptions = parse_json_list(
            review["misconceptions"]
        )

        missing = parse_json_list(
            review["missing_points"]
        )

        recent_misconceptions.extend(misconceptions)
        recent_missing_points.extend(missing)

    # PRIORITY 1 
    # MISCONCEPTIONS

    if recent_misconceptions:
        misconception = recent_misconceptions[0]

        return ReviewStrategy(
            question_type='comparison',
            difficulty=3,

            focus=(
                "Test and correct this previous missconception: " + misconception
            ),

            reason=(
                "A misconception was deteced during a previous review."
            )
        )
            

    # PRIORITY 2
    # MISSING POINTS

    if recent_missing_points:
        missing = recent_missing_points[0]

        question_type = (
            "free_recall"
            if mastery < 0.6 
            else "application"
        )

        return ReviewStrategy(
            question_type=question_type,
            difficulty=3,

            focus=(
                "Test and reinforce this missing point: " + missing
            ),

            reason=(
                "Previous answers were mostly correct but incomplete."
            )
        )

    # PRIORITY 3
    # Very low retrievability

    if retrievability < 0.6:

        return ReviewStrategy(
            question_type='free_recall',
            difficulty=2,

            focus=(
                "Check whether the learner can recall the fundamental idea without hints."
            ),

            reason=(
                "The material is not being recalled reliably."
            )
        )

    # NORMAL ADAPTATION

    if mastery < 0.3:
        return ReviewStrategy(
            question_type='free_recall',
            difficulty=2,

            focus=(
                "Test the fundamental definition and core idea"
            ),

            reason=(
                "The concept has low mastery"
            )
        )

    if mastery < 0.6:
        return ReviewStrategy(
            question_type='free_recall',
            difficulty=3,

            focus=(
                "Ask the learner to explain the concept in their own words and provide an example."
            ),

            reason=(
                "The learner has basic knowledge but mastery is still developing."
            )
        )

    if mastery < 0.8:
        return ReviewStrategy(
            question_type='application',
            difficulty=4,

            focus=(
                "Ask the learner to apply the concept in a new context or solve a problem."
            ),

            reason=(
                "The learner has good understanding but needs to practice application."
            )
        )

    return ReviewStrategy(
        question_type="comparison",
        difficulty=5,

        focus=(
            "Ask the learner to compare and contrast this concept with related concepts."
        ),

        reason=(
            "The learner has high mastery and can handle complex tasks."
        )
    )