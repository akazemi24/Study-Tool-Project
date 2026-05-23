import pdfplumber
import docx
import io
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(contents: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(contents: bytes) -> str:
    doc = docx.Document(io.BytesIO(contents))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_txt(contents: bytes) -> str:
    return contents.decode("utf-8")

def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )
    return splitter.split_text(text)

async def process_file(filename: str, contents: bytes, content_type: str) -> dict:
    if content_type == "application/pdf":
        text = extract_text_from_pdf(contents)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(contents)
    else:
        text = extract_text_from_txt(contents)
    
    chunks = chunk_text(text)
    
    return {
        "filename": filename,
        "character_count": len(text),
        "chunk_count": len(chunks),
        "preview": chunks[0] if chunks else "",
        "chunks": chunks
    }