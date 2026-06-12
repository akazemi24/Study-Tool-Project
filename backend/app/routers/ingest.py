import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db, AsyncSessionLocal
from app.models import Document, Chunk, Embedding
from app.services.file_processor import process_file
from app.services.embedding_service import generate_embeddings_batch
from app.routers.auth import get_current_user
from app.models import Document, Chunk, Embedding, User

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
    content_type: str
):
    async with AsyncSessionLocal() as db:
        try:
            result = await process_file(
                filename=filename,
                contents=contents,
                content_type=content_type
            )
            chunks = []
            for index, chunk_text in enumerate(result["chunks"]):
                chunk = Chunk(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=index
                )
                db.add(chunk)
                chunks.append(chunk)

            await db.flush()

            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await generate_embeddings_batch(chunk_texts)

            for chunk, embedding_vector in zip(chunks, embeddings):
                embedding = Embedding(
                    chunk_id=chunk.id,
                    embedding=embedding_vector
                )
                db.add(embedding)

            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="ready")
            )

            await db.commit()

        except Exception as e:
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="error")
            )
            await db.commit()
            print(f"Background task error: {e}")


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        user_id=current_user.id,
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
        content_type=file.content_type
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

@router.get("/documents")
async def get_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document)
        .where(
            Document.user_id == current_user.id,
            Document.status == "ready"
        )
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()

    return {
        "documents": [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "uploaded_at": str(doc.uploaded_at)
            }
            for doc in documents
        ]
    }