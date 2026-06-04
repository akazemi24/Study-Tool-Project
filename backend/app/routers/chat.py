import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db
from app.models import Document, Chunk, Embedding
from app.services.chat_service import get_socratic_response
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/chat", tags=["chat"])

# Pydantic request model for asking a question about a document
class ChatRequest(BaseModel):
    question: str
    document_id: uuid.UUID


@router.post("/ask")
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    doc_result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Document is not ready for querying"
        )
    # Generate embedding for the question
    question_embedding = await generate_embedding(request.question)

    embedding_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    # use sql to calculate cosine similarity between question embedding and chunk embeddings, and retrieve top 5 most similar chunks
    # slqachemy text() is used to write raw SQL queries, and :embedding and :document_id are parameters that will be passed in when executing the query
    similarity_query = text("""
        SELECT c.content, 1 - (e.embedding <=> CAST(:embedding AS vector)) as similarity
        FROM embeddings e
        JOIN chunks c ON c.id = e.chunk_id
        JOIN documents d ON d.id = c.document_id
        WHERE d.id = CAST(:document_id AS uuid)
        ORDER BY e.embedding <=> CAST(:embedding AS vector)
        LIMIT 5
    """)

    result = await db.execute(
    similarity_query,
    {"embedding": embedding_str, "document_id": str(request.document_id)}
    )
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No relevant content found for this question"
        )

    context_chunks = [row[0] for row in rows]
    similarities = [row[1] for row in rows]

    answer = await get_socratic_response(
        question=request.question,
        context_chunks=context_chunks
    )

    return {
        "question": request.question,
        "answer": answer,
        "sources_used": len(context_chunks),
        "top_similarity": round(float(similarities[0]), 3)
    }