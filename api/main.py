from fastapi import FastAPI, HTTPException

from src.database import (
    initialize_database,
    get_all_concepts_with_state,
    get_daily_review_concepts
)

from src.scheduler import (
    calculate_retrievability
)

from api.schemas import (
    ConceptsResponse,
    DailyReviewRespone,
    ReviewConceptResponse,
    QuestionResponse
)

from src.embeddings import (
    EmbeddingModel,
    generate_missing_embeddings
)

from src.review_engine import create_review_question

embeding_model = None 

app: FastAPI = FastAPI(
    title="Active Recall API",
    version="0.1.0",
    description=(
        "Adaptive learning API using RAG, active recall and spaced repetition."
    )
)

@app.on_event("startup")
def startup():
    global embeding_model
    initialize_database()

    embeding_model = EmbeddingModel()
    generate_missing_embeddings(embeding_model)

@app.get("/")
def root():
    return {
        "name": "Active Recall API",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/concepts", response_model=list[ConceptsResponse])
def get_concepts():
    rows = get_all_concepts_with_state()

    concepsts = []

    for row in rows:
        retrievability = calculate_retrievability(
            last_review=row["last_reviewed"],
            stability_days=row["stability_days"]
        )

        concept = ConceptsResponse(
            id=row["id"],
            heading=row["heading"],
            note=row["note"],

            mastery=row["mastery"],
            retrievability=retrievability,
            stability_days=row["stability_days"],

            review_count=row["review_count"],

            last_reviewed=row["last_reviewed"],
            next_review=row["next_review"]
        )

        concepsts.append(concept)

    return concepsts

@app.get("/review/today", response_model=DailyReviewRespone)
def get_today_review():
    rows = get_daily_review_concepts(limit=10)

    concepts = []

    for row in rows:
        retrievability = calculate_retrievability(
            last_review=row["last_reviewed"],
            stability_days=row["stability_days"] if "stability_days" in row.keys() else 1.0
        )

        concept = ReviewConceptResponse(
            id=row["id"],
            heading=row["heading"],
            note=row["note"],

            mastery=row["mastery"],
            retrievability=retrievability
        )

        concepts.append(concept)

    return DailyReviewRespone(
        due_count=len(concepts),
        concepst=concepts
    )

@app.post(
    "/review/{concept_id}/question",
    response_model=QuestionResponse
)
def create_question(concept_id:int):
    try:
       result = create_review_question(
           concept_id=concept_id,
            embedding_model=embeding_model
       )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    quetsion = result["question"]
    concept = result["concept"]

    return QuestionResponse(
        concept_id=concept["id"],
        question=quetsion.question,

        difficulty=quetsion.dificulty,
        question_type=quetsion.question_type,

        target_concept=concept["heading"],

        sources=result["sources"]
    )