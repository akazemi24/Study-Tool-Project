import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Document, Chunk
from app.services.file_processor import process_file

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

MAX_FILE_SIZE = 10 * 1024 * 1024


async def save_document_to_db(
    document_id: uuid.UUID,
    filename: str,
    contents: bytes,
    content_type: str,
    db: AsyncSession
):
    try:
        result = await process_file(
            filename=filename,
            contents=contents,
            content_type=content_type
        )

        for index, chunk_text in enumerate(result["chunks"]):
            chunk = Chunk(
                document_id=document_id,
                content=chunk_text,
                chunk_index=index
            )
            db.add(chunk)

        await db.execute(
            Document.__table__.update()
            .where(Document.id == document_id)
            .values(status="ready")
        )

        await db.commit()

    except Exception as e:
        await db.execute(
            Document.__table__.update()
            .where(Document.id == document_id)
            .values(status="error")
        )
        await db.commit()
        raise e


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Please upload a PDF, TXT, or DOCX file."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )

    document = Document(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        filename=file.filename,
        status="processing"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    background_tasks.add_task(
        save_document_to_db,
        document_id=document.id,
        filename=file.filename,
        contents=contents,
        content_type=file.content_type,
        db=db
    )

    return {
        "document_id": str(document.id),
        "filename": file.filename,
        "status": "processing",
        "message": "File uploaded successfully. Processing in background."
    }


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "status": document.status
    }