from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_processor import process_file

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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
    
    result = await process_file(filename=file.filename, contents=contents, content_type=file.content_type)
    
    return result