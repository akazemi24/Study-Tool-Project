import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Document, Chunk, Flashcard
from app.services.flashcard_service import generate_flashcards_from_chunks
from app.routers.auth import get_current_user
from app.models import Document, Chunk, Flashcard, User

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

# create flashcards
@router.post("/generate/{document_id}")
async def generate_flashcards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = doc_result.scalar_one_or_none()

    # Check if the document exists
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Ensure the document is in "ready" status before generating flashcards
    if document.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready for processing. Current status: {document.status}"
        )
    
    existing = await db.execute(
        select(Flashcard).where(
            Flashcard.document_id == document_id,
            Flashcard.user_id == current_user.id
        )
    )

    # Check if flashcards already exist for this document
    if existing.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Flashcards already generated for this document. Use GET /flashcards/{document_id} to retrieve them."
        )

    chunks_result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        # retrieve chunks in original document order
        .order_by(Chunk.chunk_index)
    )
    # unwraps SQLAlchemy result to get list of Chunk objects
    chunks = chunks_result.scalars().all()

    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for this document")

    chunk_texts = [chunk.content for chunk in chunks]
    flashcard_data = await generate_flashcards_from_chunks(chunk_texts)

    saved_flashcards = []
    for card in flashcard_data:
        flashcard = Flashcard(
            document_id=document_id,
            user_id=current_user.id,
            question=card["question"],
            answer=card["answer"]
        )
        db.add(flashcard)
        saved_flashcards.append(flashcard)

    await db.commit()

    for card in saved_flashcards:
        await db.refresh(card)

    return {
        "document_id": str(document_id),
        "flashcard_count": len(saved_flashcards),
        "flashcards": [
            {
                "id": str(card.id),
                "question": card.question,
                "answer": card.answer
            }
            for card in saved_flashcards
        ]
    }

# get flashcards for a document
@router.get("/{document_id}")
async def get_flashcards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Flashcard)
        .where(
            Flashcard.document_id == document_id,
            Flashcard.user_id == current_user.id
        )
        .order_by(Flashcard.created_at)
    )
    flashcards = result.scalars().all()

    if not flashcards:
        raise HTTPException(
            status_code=404,
            detail="No flashcards found for this document"
        )

    return {
        "document_id": str(document_id),
        "flashcard_count": len(flashcards),
        "flashcards": [
            {
                "id": str(card.id),
                "question": card.question,
                "answer": card.answer
            }
            for card in flashcards
        ]
    }