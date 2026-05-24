from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIMENSIONS = 384


def generate_embedding(text: str) -> list[float]:
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(texts, convert_to_tensor=False)
    return [emb.tolist() for emb in embeddings]