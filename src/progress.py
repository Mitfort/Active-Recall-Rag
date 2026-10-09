from src.database import (
    get_all_learning_states
)

states = get_all_learning_states()

for state in states:
    print(
        f"""
    {state['heading']}
    Note: {state['note']}

    Mastery: 
    {state['mastery']:.0%}

    Reviews: 
    {state['review_count']}

    Correct:
    {state['correct_count']}

    Next:
    {state['next_review']}

    ------------------------
"""
    )