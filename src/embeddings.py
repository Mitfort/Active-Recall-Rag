from sentence_transformers import SentenceTransformer
import numpy as np

from src.database import get_concepts_without_embedding, save_embedding

MODEL_NAME = "all-MiniLM-L6-v2"

class EmbeddingModel:
    def __init__(self):
        print(f"Loading embedding model: {MODEL_NAME}")

        self.model = SentenceTransformer(MODEL_NAME)

    def embed(self, text: str) -> np.ndarray:
        embedding = self.model.encode(text, normalize_embeddings=True)

        return embedding

def generate_missing_embeddings(embedding_model: EmbeddingModel) -> None:
    concepts = get_concepts_without_embedding()

    if not concepts:
        print("No concepts without embeddings found.")
        return

    print(f"Generating embeddings for {len(concepts)} concepts...")

    for concept in concepts:
        text = (concept['heading'] + '\n' + concept['content'])

        embedding = embedding_model.embed(text)

        save_embedding(concept['id'], embedding.tolist())

        print(f"Embedded: {concept['heading']}")