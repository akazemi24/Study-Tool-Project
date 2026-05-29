from fastembed import TextEmbedding

model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

EMBEDDING_DIMENSIONS = 384


def generate_embedding(text: str) -> list[float]:
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    embeddings = list(model.embed(texts))
    return [emb.tolist() for emb in embeddings]