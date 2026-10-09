from src.evaluator import evaluate_answer

evaluation = evaluate_answer(
    question=(
        "How does a decision tree choose a split?"
    ),

    expected_answer=(
        "It evaluates candidate splits using criteria "
        "such as Gini impurity or information gain."
    ),

    student_answer=(
        "It checks different splits and chooses the one "
        "that makes the resulting groups more pure."
    ),

    context=(
        "Decision trees recursively split data. "
        "Splits can be evaluated using Gini impurity "
        "or information gain."
    ),
)

print(evaluation)
