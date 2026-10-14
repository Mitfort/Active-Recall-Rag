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
    attempt_id:int
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

class WeakConceptResponse(BaseModel):
    id:int
    heading:str
    note:str

    mastery:float
    retrievability:float

class ActivityDayResponse(BaseModel):
    date:str
    reviews:int
    average_correctness:float | None

class DashboardResponse(BaseModel):
    due_today:int

    total_concepts:int
    new_concepts:int

    average_mastery:float
    average_retrievability:float

    recent_accuracy:float | None

    reviews_last_7_days:int

    weakest: list[WeakConceptResponse]
    activity: list[ActivityDayResponse]

class ReviewHistoryItem(BaseModel):
    id:int
    concept_id:int

    heading:str
    note:str

    question:str

    ai_correctness:float | None
    combined_score:float | None

    confidence:int | None

    scheduler_rating:str

    reviewed_at:str

class ReviewHistoryResponse(BaseModel):
    reviews: list[ReviewHistoryItem]