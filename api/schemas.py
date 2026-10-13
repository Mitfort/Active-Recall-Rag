from pydantic import BaseModel
from typing import Optional 

class ConceptsResponse(BaseModel):
    id:int
    heading:str 
    note:str 

    mastery:float 
    retrievability:float
    stability_days:float

    review_count:int

    last_reviewed:Optional[str] = None
    next_review:Optional[str] = None

class ReviewConceptResponse(BaseModel):
    id:int
    heading:str
    note:str

    mastery:float
    retrievability:float

class DailyReviewRespone(BaseModel):
    due_count:int
    concepst: list[ReviewConceptResponse]

class QuestionResponse(BaseModel):
    concept_id:int

    question:str 

    difficulty:int
    question_type:str

    target_concept:str

    sources: list[dict]

class AnswerRequest(BaseModel):
    answer:str
    confidence:int 

class AnswerResponse(BaseModel):
    correctness:float
    verdict:str 

    feedback:str

    missing_points:list[str]
    missconceptions:list[str]

    combined_score:float

    scheduler_rating:str 

    mastery_before:float
    mastery_after:float

    stability_before:float
    stability_after:float

    next_review:str 