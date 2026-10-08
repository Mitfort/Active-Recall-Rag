from pydantic import BaseModel, Field 
from typing import Literal

class QuizQuestion(BaseModel):
    question: str
    expected_answer: str

    dificulty: int = Field(
        ge=1,
        le=5
    )

    question_type: Literal[
        "free_recall",
        "application",
        "comparison",
        "muultiple_choice"
    ]

    concept_ids: list[int]