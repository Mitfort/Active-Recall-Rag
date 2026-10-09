from typing import Literal

from ollama import chat
from pydantic import BaseModel, Field

MODEL_NAME = "qwen3:4b-instruct"

class AnswerEvaluation(BaseModel):
    correctness: float = Field(
        ge=0.0,
        le=1.0
    )

    verdict: Literal[
        'incorrect',
        'partial',
        'correct'
    ]

    missing_points: list[str]

    missconceptions: list[str]

    feedback: str 


SYSTEM_PROMPT = """
You are an academic professor and your task is to evaluate the correctness of a student's answer to a question.

Evaluate understanding, not exact wording.

Rules: 
1. Compare the student's answer to the expected answer and supplied learning context.

2. Accept paraphrases and semantically equivalent answers.

3. Do not require the student to reproduce the expected answer word-to-word.

4. Extra correct information should not reduce the score.

5. Identify important missing ideas.

6. Identify actual misconceptions separately from missing information.

7. Provide a correctness score between 0 and 1, where 0 is completely incorrect and 1 is completely correct.

Suggested interpretation:
0.00 - 0.30:
Mostly incorrect or demonstrates little understanding.

0.30 - 0.60:
Partial understanding but important concepts are missing.

0.60 - 0.85:
Mostly correct with some missing details.

0.85 - 1.00:
Strong understanding.

Be concise and educational.
"""

def evaluate_answer(
    question: str,
    expected_answer: str,
    student_answer: str,
    context: str
) -> AnswerEvaluation:
    prompt = f"""
Question: {question}
Expected Answer: {expected_answer}
Student Answer: {student_answer}
Context: {context}

Evaluate the student's understanding.
"""

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        format=AnswerEvaluation.model_json_schema(),

        options={
            'temperature': 0.1,
        }
    )

    return AnswerEvaluation.model_validate_json(
        response.message.content
    )