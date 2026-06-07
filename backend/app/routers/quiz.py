import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Flashcard, QuizProgress
from app.services.quiz_service import sm2
from app.routers.auth import get_current_user
from app.models import Flashcard, QuizProgress, User

router = APIRouter(prefix="/quiz", tags=["quiz"])

class RatingRequest(BaseModel):
    flashcard_id: uuid.UUID
    rating: int


@router.get("/due/{document_id}")
async def get_due_cards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # get the correct flashcards for this document and user
    flashcards_result = await db.execute(
        select(Flashcard).where(
            Flashcard.document_id == document_id,
            Flashcard.user_id == current_user.id
        )
    )
    flashcards = flashcards_result.scalars().all()

    if not flashcards:
        raise HTTPException(status_code=404, detail="No flashcards found for this document")

    flashcard_ids = [card.id for card in flashcards]

    progress_result = await db.execute(
        select(QuizProgress).where(
            QuizProgress.flashcard_id.in_(flashcard_ids),
            QuizProgress.user_id == current_user.id
        )
    )
    # create a dict of flashcard_id to progress for easy lookup
    existing_progress = {p.flashcard_id: p for p in progress_result.scalars().all()}

    due_cards = []

    for flashcard in flashcards:
        progress = existing_progress.get(flashcard.id)

        # no progress record -> card is new, put in review queue
        if progress is None:
            due_cards.append({
                "flashcard_id": str(flashcard.id),
                "question": flashcard.question,
                "answer": flashcard.answer,
                "is_new": True,
                "interval_days": 1,
                "ease_factor": 2.5
            })
        # existing progress record -> check if card is due for review (next_review is None for new cards, or next_review <= today for due cards)
        elif progress.next_review is None or progress.next_review <= date.today():
            due_cards.append({
                "flashcard_id": str(flashcard.id),
                "question": flashcard.question,
                "answer": flashcard.answer,
                "is_new": False,
                "interval_days": progress.interval_days,
                "ease_factor": progress.ease_factor
            })

    return {
        "document_id": str(document_id),
        "due_count": len(due_cards),
        "cards": due_cards
    }


@router.post("/rate")
async def rate_card(
    request: RatingRequest,
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if request.rating < 0 or request.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 0 and 5"
        )

    flashcard_result = await db.execute(
        select(Flashcard).where(Flashcard.id == request.flashcard_id)
    )
    flashcard = flashcard_result.scalar_one_or_none()

    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    progress_result = await db.execute(
        select(QuizProgress).where(
            QuizProgress.flashcard_id == request.flashcard_id,
            QuizProgress.user_id == current_user.id
        )
    )
    progress = progress_result.scalar_one_or_none()

    if progress is None:
        new_ease, new_interval, next_review = sm2(2.5, 1, request.rating)
        progress = QuizProgress(
            user_id=current_user.id,
            flashcard_id=request.flashcard_id,
            ease_factor=new_ease,
            interval_days=new_interval,
            next_review=next_review
        )
        db.add(progress)
    else:
        new_ease, new_interval, next_review = sm2(
            progress.ease_factor,
            progress.interval_days,
            request.rating
        )
        progress.ease_factor = new_ease
        progress.interval_days = new_interval
        progress.next_review = next_review

    await db.commit()
    await db.refresh(progress)

    return {
        "flashcard_id": str(request.flashcard_id),
        "rating": request.rating,
        "new_interval_days": progress.interval_days,
        "new_ease_factor": round(progress.ease_factor, 2),
        "next_review": str(progress.next_review)
    }