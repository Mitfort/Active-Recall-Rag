from src.database import (
    get_all_learning_states
)

from src.scheduler import calculate_retrievability

states = get_all_learning_states()

for state in states:
    retrievability = calculate_retrievability(
        last_review=state['last_reviewed'],
        stability_days=state['stability_days']
    )

    print(
        f"""
    {state['heading']}
    Note: {state['note']}

    Mastery: 
    {state['mastery']:.0%}
    
    Stability:
    {state['stability_days']:.0f} days

    Retrievability:
    {retrievability:.0%}

    Reviews: 
    {state['review_count']}

    Correct:
    {state['correct_count']}

    Next:
    {state['next_review']}

    ------------------------
"""
    )