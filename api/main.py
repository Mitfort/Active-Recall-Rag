from fastapi import FastAPI, HTTPException, Query

from src.database import (
    initialize_database,
    get_all_concepts_with_state,
    get_daily_review_concepts,
    create_review_attempt,
    get_review_attempt,
    complete_review_attempt,
    get_learning_state,
    save_review,
    sync_note,
    count_due_concepts,
    get_recent_review_stats,
    get_review_activity,
    get_review_history
)

from src.scheduler import (
    calculate_retrievability,
    calculate_learning_score,
    update_memory_state
)

from api.schemas import (
    AnswerRequest,
    AnswerResponse,
    ConceptsResponse,
    DailyReviewRespone,
    ReviewConceptResponse,
    QuestionResponse,
    
    DashboardResponse,
    WeakConceptResponse,
    ActivityDayResponse,

    ReviewHistoryItem,
    ReviewHistoryResponse
)

from src.embeddings import (
    EmbeddingModel,
    generate_missing_embeddings
)

from src.review_engine import create_review_question
from src.evaluator import evaluate_answer

from src.ingestion import load_notes

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
        attempt_id=create_review_attempt(
            concept_id=concept["id"],
            question=quetsion.question,
            expected_answer=quetsion.expected_answer,
            difficulty=quetsion.dificulty,
            question_type=quetsion.question_type,
            context=quetsion['context'],
            sources=result["sources"]
        ),

        concept_id=concept["id"],
        question=quetsion.question,

        difficulty=quetsion.dificulty,
        question_type=quetsion.question_type,

        target_concept=concept["heading"],

        sources=result["sources"]
    )

@app.post(
    "/review/{attempt_id}/answer",
    response_model=AnswerResponse
)
def submit_answer(
    attempt_id:int,
    request:AnswerRequest
): 
    attempt = get_review_attempt(attempt_id=attempt_id)

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail=f"Review attempt with ID {attempt_id} not found or already completed."
        )

    if request.confidence not in [1,2,3,4,5]:
        raise HTTPException(
            status_code=400,
            detail="Confidence must be an integer between 1 and 5."
        )

    evaluation = evaluate_answer(
        question=attempt["question"],
        expected_answer=attempt["expected_answer"],
        student_answer=request.answer,
        context=attempt["context"],
    )

    combined_score, rating = calculate_learning_score(
        correctness=evaluation.correctness,
        confidence=request.confidence,
        difficulty=attempt["difficulty"]
    )

    state = get_learning_state(concept_id=attempt["concept_id"])

    new_mastery, new_stability, next_review = update_memory_state(
        current_mastery=state["mastery"],
        current_stability=state["stability_days"],
        combined_score=combined_score
    )

    import json 

    sources = json.loads(attempt["sources"]) if attempt["sources"] else []

    save_review(
        concept_id=attempt["concept_id"],
        question=attempt["question"],
        expected_answer=attempt["expected_answer"],
        user_answer=request.answer,
        rating=rating,
        new_mastery=new_mastery,
        new_stability=new_stability,
        next_review=next_review,
        ai_correctness=evaluation.correctness,
        ai_feedback=evaluation.feedback,
        missing_points=evaluation.missing_points,
        misconceptions=evaluation.missconceptions,
        user_confidence=request.confidence,
        combined_score=combined_score,
        source_provenance=sources
    )


    complete_review_attempt(attempt_id=attempt_id)

    rating_names = {
        1: "Again",
        2: "Hard",
        3: "Good",
        4: "Easy",
        5: "Very Easy"
    }

    return AnswerResponse(
        correctness=evaluation.correctness,
        verdict=evaluation.verdict,

        feedback=evaluation.feedback,

        missing_points=evaluation.missing_points,
        missconceptions=evaluation.missconceptions,

        combined_score=combined_score,

        scheduler_rating=rating_names[rating],

        mastery_before=state["mastery"],
        mastery_after=new_mastery,

        stability_before=state["stability_days"],
        stability_after=new_stability,

        next_review=next_review.isoformat()
    )

@app.post("/notes/sync")
def sync_notes():
    notes = load_notes("data/notes")

    results = []

    for note in notes:
        status = sync_note(note)

        results.append(
            {
                "file": note.file_name,
                "status": status
            }
        )

    generate_missing_embeddings(embeding_model)

    return {
        "notes": results
    }

@app.get(
    "/dashboard",
    response_model=DashboardResponse
)
def get_dashboard():
    concepts = get_all_concepts_with_state()

    due_today = count_due_concepts()

    recent_stats = get_recent_review_stats(days=7)

    activity_rows = get_review_activity(days=7)

    total_concepts = len(concepts)

    new_concepts = sum(1 for c in concepts if c['review_count'] == 0)


    # Calculate current memory state

    concept_states = []

    for concept in concepts:
        retrievability = calculate_retrievability(
            last_review=concept["last_reviewed"],
            stability_days=concept["stability_days"]
        )

        concept_states.append({
            "id": concept["id"],
            "heading": concept["heading"],
            "note": concept["note"],
            "mastery": concept["mastery"],
            "retrievability": retrievability,
            "review_count": concept["review_count"],
        })


    # Averages 

    if concept_states:
        average_mastery = sum(
            concept["mastery"] for concept in concept_states
        ) / len(concept_states)

        average_retrievability = sum(
            concept["retrievability"] for concept in concept_states
        ) / len(concept_states)

    else:
        average_mastery = 0.0
        average_retrievability = 0.0


    ## Weak concepts ##
    
    # We skip concepts that are new 
    reviewed_concepts = [c for c in concept_states if c["review_count"] > 0]

    for concept in reviewed_concepts:
        concept['knowledge_strength'] = 0.6 * concept['mastery'] + 0.4 * concept['retrievability']

    reviewed_concepts.sort(key=lambda c: c['knowledge_strength'])

    weakest = [
        WeakConceptResponse(
            id=c["id"],
            heading=c["heading"],
            note=c["note"],
            mastery=c["mastery"],
            retrievability=c["retrievability"]
        )
        for c in reviewed_concepts[:5]
    ]

    ## Activity ##

    activity = [
        ActivityDayResponse(
            date=row["day"],
            reviews=row["reviews"],
            average_correctness=row["average_correctness"],
        )
        for row in activity_rows
    ]

    return DashboardResponse(
        due_today=due_today,

        total_concepts=total_concepts,
        new_concepts=new_concepts,

        average_mastery=average_mastery,
        average_retrievability=average_retrievability,

        recent_accuracy=recent_stats["average_correctness"],

        reviews_last_7_days=recent_stats["review_count"],

        weakest=weakest,
        activity=activity
    )


@app.get(
    "/review/history",
    response_model=ReviewHistoryResponse
)
def review_history(
    limit:int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of review history items to return."
    ),

    offset:int = Query(
        default=0,
        ge=0,
        description="Number of review history items to skip."
    )
):
    rows = get_review_history(limit=limit, offset=offset)

    rating_names = {
        1: "Again",
        2: "Hard",
        3: "Good",
        4: "Easy",
        5: "Very Easy"
    }

    reviews = []

    for row in rows:
        reviews.append(
            ReviewHistoryItem(
                id=row["id"],
                concept_id=row["concept_id"],

                heading=row["heading"],
                note=row["note"],

                question=row["question"],

                ai_correctness=row["ai_correctness"],
                combined_score=row["combined_score"],

                confidence=row["user_confidence"],

                scheduler_rating=rating_names.get(row["rating"], "Unknown"),

                reviewed_at=row["reviewed_at"]
            )
        )

    return ReviewHistoryResponse(
        reviews=reviews,
    )