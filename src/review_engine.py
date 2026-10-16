from src.database import (
    get_concept,
    get_learning_state,
    get_recent_reviews,
)

from src.retrieval import semantic_search

from src.context import build_enriched_context

from src.adaptive import choose_review_strategy

from src.generator import generate_question

from src.external_knowledge import (
    WikipediaProvider,
    should_use_external_knowledge
)

def create_review_question(
    concept_id: int,
    embedding_model
):

    concept = get_concept(concept_id)

    if concept is None:
        raise ValueError("Concept not found.")

    state = get_learning_state(concept_id)

    recent_reviews = get_recent_reviews(concept_id, limit=5)

    strategy = choose_review_strategy(
        state=state,
        recent_reviews=recent_reviews
    )

    query = (concept['heading'] + "\n" + concept["content"])

    supporting_result = semantic_search(
        query=query,
        embedding_model=embedding_model,
        top_k=4
    )

    supporting_result = [
        result for result in supporting_result
        if result['id'] != concept['id']
    ]

    target_result = {
        "id": concept['id'],
        "note": concept['note'],
        "heading": concept['heading'],
        "content": concept['content'],
        "score": 1.0
    }

    personal_results = [target_result] + supporting_result[:3]

    use_external = should_use_external_knowledge(
        target_content=concept['content'],
        supporting_results=supporting_result,
        difficulty=strategy.difficulty,
        mode="when_needed"
    )

    if use_external:
        wikipedia_provider = WikipediaProvider(language="en")

        try:
            external_sources = wikipedia_provider.search(
                query=(
                    f"{concept['heading']} " 
                    f"{concept['note']}"
                ),
                limit=2
            )
        except Exception as e:
            print(f"Error fetching external knowledge: {e}")
            external_sources = []

    context = build_enriched_context(
        personal_results=personal_results,
        external_sources=external_sources
    )

    question = generate_question(
        context=context,
        topic=(
            f"Main concept: "
            f"{concept['heading']} "   
        ),
        question_type=strategy.question_type,
        difficulty=strategy.difficulty,
        focus=strategy.focus
    )

    sources = []

    for result in personal_results:
        sources.append({
            "source_type": "personal_note",
            "concept_id": result["id"],
            "name": result["heading"],
            "note": result["note"],
        })

    for source in external_sources:
        sources.append({
            "source_type": "external_reference",
            "provider": source.provider,
            "name": source.title,
            "url": source.url,
        })

    return {
        "concept": concept,
        "question": question,
        "context": context,
        "strategy": strategy,
        "sources": sources
    }