import json 

import numpy as np

from src.database import (
    get_note_embedding_rows
)

def build_note_vectors():
    """
    Creates one normalized semantic vector
    for every note by avereging its concept embeddings.
    """

    rows = get_note_embedding_rows()

    note_data = {}

    for row in rows:
        note_id = row['note_id']
        embedding = np.array(json.loads(row['embedding']),dtype=np.float32)

        if note_id not in note_data:
            note_data[note_id] = {
                "title": row['note_title'],
                "subject": row['subject'],
                "embeddings": []
            }

        note_data[note_id]["embeddings"].append(embedding)

    note_vectors = {}

    for note_id, data in note_data.items():

        matrix = np.stack(data["embeddings"])

        vector = np.mean(matrix, axis=0)

        norm = np.linalg.norm(vector)

        if norm == 0:
            continue 

        vector = vector / norm

        note_vectors[note_id] = {
            "title": data["title"],
            "subject": data["subject"],
            "vector": vector
        }

    return note_vectors

def find_semantic_note_relations(
    explicit_edges: list[dict],
    threshold: float = 0.72,
    max_neighbors: int = 3
):
    """
    Returns suggested semantic relations between notes.
    
    Semantic relations:
    - are NOT persistent
    - exclude explicit wikilinks
    - must exceed similarity threshold
    - are limited to avoid graph clutter
    """

    note_vectors = build_note_vectors()

    note_ids = list(note_vectors.keys())

    ### Explicit connections should not appear
    # as semantic suggestions

    explicit_pairs = set()

    for edge in explicit_edges:
        pair = tuple(
            sorted((int(edge['source']),int(edge["target"])))
        )

        explicit_pairs.add(pair)

    candidates = []

    ### Compare every note pair
    # Fine for a normal personal notes

    for i in range(len(note_ids)):
        for j in range(i+1, len(note_ids)):

            source_id = note_ids[i]
            target_id = note_ids[j]

            pair = (source_id, target_id)

            if pair in explicit_pairs:
                continue

            source_vector = (
                note_vectors[source_id]["vector"]
            )

            target_vector = (
                note_vectors[target_id]["vector"]
            )

            similarity = float(
                np.dot(source_vector, target_vector)
            )

            if similarity < threshold:
                continue

            candidates.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "type": "semantic",
                    "score": similarity
                }
            )

    ### Highest-confidence relations first 

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    ### Prevent every note from connecting
    # to every other note

    degree = {
        note_id: 0
        for note_id in note_ids
    }

    accepted = []

    for edge in candidates:

        source = edge["source"]
        target = edge["target"]

        if degree[source] >= max_neighbors:
            continue

        if degree[target] >= max_neighbors:
            continue

        accepted.append(edge)

        degree[source] += 1
        degree[target] += 1

    return accepted