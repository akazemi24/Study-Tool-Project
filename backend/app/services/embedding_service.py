from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

EMBEDDING_DIMENSIONS = 1536


async def generate_embedding(text: str) -> list[float]:
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    response.data.sort(key=lambda x: x.index)
    return [item.embedding for item in response.data]