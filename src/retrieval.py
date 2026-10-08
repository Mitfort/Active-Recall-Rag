import json
import numpy as np

from src.database import get_concepts_with_embeddings
from src.embeddings import EmbeddingModel

def cosine_similarity(
        vector_a: np.ndarray,
        vector_b: np.ndarray
) -> float:
    """
    Calculate the cosine similarity between two vectors.

    Args:
        vector_a (np.ndarray): The first vector.
        vector_b (np.ndarray): The second vector.

    Returns:
        float: The cosine similarity between the two vectors.
    """

    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def semantic_search(
    query: str,
    embedding_model: EmbeddingModel,
    top_k: int = 3
):
    query_embedding = embedding_model.embed(query)

    concepts = get_concepts_with_embeddings()

    results = []

    for concept in concepts:
        concept_embedding = np.array(
            json.loads(concept['embedding'])
        )

        score = cosine_similarity(query_embedding, concept_embedding)

        results.append(
            {
                "id": concept['id'],
                "note": concept['note_title'],
                "heading": concept['heading'],
                "content": concept['content'],
                "score": score
            }
        )

    results.sort(
        key=lambda result: result['score'],
        reverse=True
    )

    return results[:top_k]
