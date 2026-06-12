# Study Tool — AI-Powered Study Assistant

An end-to-end full-stack application that transforms lecture notes and textbook PDFs into an interactive study experience. Upload a document and get AI-generated flashcards, a Socratic Q&A chatbot grounded in your notes via RAG, and a spaced repetition quiz engine.

**Live Demo:** [https://main.dhri2rrceau36.amplifyapp.com](https://main.dhri2rrceau36.amplifyapp.com)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, React Router |
| Backend | FastAPI (Python), Gunicorn + Uvicorn workers |
| Database | PostgreSQL + pgvector (vector similarity search) |
| Migrations | Alembic |
| AI | Anthropic Claude API (Haiku for flashcards, Sonnet for chat) |
| Embeddings | OpenAI `text-embedding-3-small` (1536-dim vectors) |
| Auth | Google OAuth 2.0 + JWT (python-jose) |
| Deployment | AWS Elastic Beanstalk, AWS Amplify, AWS RDS, AWS CloudFront |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Amplify                          │
│                    React + Tailwind (SPA)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      AWS CloudFront                         │
│                  (HTTPS termination, CDN)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Elastic Beanstalk (EC2)                    │
│         FastAPI — 4 Uvicorn async workers                   │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ /ingest     │  │ /flashcards  │  │ /chat              │ │
│  │ /auth       │  │ /quiz        │  │ (RAG pipeline)     │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘ │
└─────────┼────────────────┼──────────────────── ┼───────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS RDS PostgreSQL                       │
│           pgvector extension for embedding storage          │
│                                                             │
│  users │ documents │ chunks │ embeddings │ flashcards       │
│  quiz_progress                                              │
└─────────────────────────────────────────────────────────────┘
          │                                     │
          ▼                                     ▼
┌──────────────────┐                ┌───────────────────────┐
│  Anthropic API   │                │     OpenAI API        │
│  Claude Haiku    │                │  text-embedding-3     │
│  Claude Sonnet   │                │  -small (1536-dim)    │
└──────────────────┘                └───────────────────────┘
```

---

## Features

- **Document ingestion** — Upload PDF, DOCX, or TXT files. Text is extracted, cleaned, chunked with 500-token overlapping windows, embedded, and stored in pgvector.
- **AI flashcard generation** — Claude Haiku reads all document chunks and generates conceptual Q&A pairs targeting understanding over memorization.
- **Socratic chat (RAG)** — User questions are embedded and matched against document chunks via cosine similarity. Top-5 retrieved chunks are injected into a Claude Sonnet prompt as grounded context.
- **Spaced repetition quiz** — SM-2 algorithm schedules card reviews based on user ratings (0–5). Ease factor and interval update per review, drifting easy cards to weeks/months between sessions.
- **Google OAuth + JWT auth** — Users sign in with Google. Backend verifies ID token, creates/looks up user, issues a signed JWT. All endpoints protected via `Depends(get_current_user)`.
- **Multi-document support** — Users can upload and switch between multiple documents, each with independent flashcard sets and quiz progress.
- **Async background processing** — File processing (extraction → chunking → embedding) runs via FastAPI `BackgroundTasks` so uploads return immediately with a document ID the frontend polls.

---

## RAG Pipeline

```
User question
     │
     ▼
OpenAI text-embedding-3-small
     │
     ▼ 1536-dim vector
pgvector cosine similarity search
  SELECT chunks WHERE document_id = ?
  ORDER BY embedding <=> query_vector
  LIMIT 5
     │
     ▼ top-5 relevant chunks
Claude Sonnet (claude-sonnet-4-5)
  System: "Answer using ONLY the provided context..."
  Context: [chunk_1] [chunk_2] ... [chunk_5]
  Question: user's question
     │
     ▼
Grounded answer
```

---

## Database Schema

```
users           — id, email, name, google_id, avatar_url, created_at
documents       — id, user_id, filename, s3_key, status, uploaded_at
chunks          — id, document_id, content, page_num, chunk_index
embeddings      — id, chunk_id, embedding vector(1536)
flashcards      — id, document_id, user_id, question, answer, created_at
quiz_progress   — id, user_id, flashcard_id, ease_factor, interval_days,
                  next_review, last_reviewed
```

`chunks` and `embeddings` are separated intentionally — chunks are human-readable content displayed in citations, embeddings are vectors for retrieval. This allows re-embedding with a different model without touching the chunks table.

---

## Local Development

### Prerequisites

- Python 3.12
- Node.js 22+
- PostgreSQL with pgvector extension
- Anthropic API key
- OpenAI API key
- Google OAuth 2.0 credentials

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

**Backend `.env`:**
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/studytool
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...
```

**Frontend `.env`:**
```
VITE_GOOGLE_CLIENT_ID=...
VITE_API_URL=http://localhost:8000   # omit for production
```

---

## Project Structure

```
study-tool-project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── routers/
│   │   │   ├── auth.py          # Google OAuth + JWT
│   │   │   ├── ingest.py        # File upload + background processing
│   │   │   ├── flashcards.py    # Flashcard generation + retrieval
│   │   │   ├── chat.py          # RAG-powered Q&A
│   │   │   └── quiz.py          # SM-2 spaced repetition
│   │   └── services/
│   │       ├── auth_service.py      # JWT create/verify
│   │       ├── embedding_service.py # OpenAI embeddings
│   │       ├── file_processor.py    # PDF/DOCX/TXT extraction + chunking
│   │       └── flashcard_service.py # Claude flashcard generation
│   ├── migrations/              # Alembic migration files
│   ├── Procfile                 # Gunicorn startup command
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── Navbar.jsx
    │   ├── pages/
    │   │   ├── LoginPage.jsx
    │   │   ├── UploadPage.jsx    # Document list + upload
    │   │   ├── FlashcardsPage.jsx
    │   │   ├── ChatPage.jsx
    │   │   └── QuizPage.jsx
    │   └── services/
    │       └── api.js            # Axios instance + auth interceptors
    └── public/
```

---

## Deployment

| Service | Purpose |
|---|---|
| AWS Elastic Beanstalk | FastAPI backend (Python 3.12, single EC2 instance) |
| AWS RDS | PostgreSQL 16 with pgvector extension |
| AWS CloudFront | HTTPS termination + CDN in front of EB |
| AWS Amplify | React frontend with GitHub CI/CD |

Every push to `main` triggers an automatic Amplify rebuild. Backend deploys via `eb deploy` from the CLI.

---

## Author

Armita Kazemi — [GitHub](https://github.com/akazemi24) — Princeton University, CS '26