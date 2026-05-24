import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="user")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="processing")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_num: Mapped[int] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    embedding: Mapped["Embedding"] = relationship(back_populates="chunk", uselist=False)

class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(384))

    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="flashcards")
    user: Mapped["User"] = relationship(back_populates="flashcards")
    quiz_progress: Mapped["QuizProgress"] = relationship(back_populates="flashcard", uselist=False)

class QuizProgress(Base):
    __tablename__ = "quiz_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    flashcard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcards.id"), nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    next_review: Mapped[datetime] = mapped_column(Date, nullable=True)
    last_reviewed: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    flashcard: Mapped["Flashcard"] = relationship(back_populates="quiz_progress")