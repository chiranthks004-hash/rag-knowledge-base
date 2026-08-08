# Enterprise AI Knowledge Base (RAG)

Upload PDF documents and ask questions about them in plain English. The app retrieves the most relevant passages using semantic (vector) search and generates a grounded answer — citing which document it came from — instead of relying on the AI's general training knowledge.

This is a full-stack Retrieval-Augmented Generation (RAG) system built to mirror the architecture used in production AI products today.

## Architecture

```
                     +---------------------------------------+
                     |            React Frontend              |
                     |     (Vite, upload UI, chat interface)  |
                     +-------------------+---------------------+
                                         |
                                         v
                     +-------------------+---------------------+
                     |         FastAPI Backend API             |
                     +---------+-------------------+-----------+
                               |                   |
            +------------------+                   +------------------+
            v                                                         v
+-----------+-----------+                                 +-----------+-----------+
|      SQLite / SQL      |                                 |      ChromaDB         |
| (documents, chat       |                                 | (vector search over   |
|  history metadata)     |                                 |  document chunks)     |
+-------------------------+                                 +-----------+-----------+
                                                                        |
                                                                        v
                                                            +-----------+-----------+
                                                            |     Groq LLM API      |
                                                            | (answer generation)   |
                                                            +------------------------+
```

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, Vite |
| Vector search | ChromaDB |
| Embeddings | sentence-transformers (local, free) |
| LLM | Groq (llama-3.1-8b-instant, free tier) |
| Relational data | SQLite (swappable for PostgreSQL) |
| Orchestration | LangChain |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |

## How it works

1. **Upload** — a PDF is uploaded, saved, and its text extracted (`pypdf`)
2. **Chunk** — the extracted text is split into overlapping chunks (`LangChain` text splitter)
3. **Embed** — each chunk is converted into a vector embedding (`sentence-transformers`) and stored in **ChromaDB**
4. **Ask** — a question is embedded the same way, and ChromaDB returns the most semantically similar chunks
5. **Generate** — those chunks are inserted into a prompt and sent to an LLM (**Groq**), which generates an answer grounded only in the retrieved text
6. **Cite** — the response includes which document(s) the answer came from

## Running locally with Docker (recommended)

**Requirements:** Docker Desktop, a free [Groq API key](https://console.groq.com)

```bash
# 1. Add your Groq API key
cp backend/.env.example backend/.env
# edit backend/.env and add: GROQ_API_KEY=gsk_your-key-here

# 2. Build and start both services
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

Uploaded documents, the database, and the vector store persist across restarts via a Docker named volume.

## Running locally without Docker (development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # then add your GROQ_API_KEY
uvicorn app.main:app --reload
```

**Frontend** (in a second terminal):
```bash
cd frontend
npm install
npm run dev
```

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload a PDF, extract text, chunk, and embed it |
| GET | `/documents` | List all uploaded documents and their status |
| GET | `/search` | Raw vector search (debugging/testing) |
| POST | `/chat` | Ask a question, get a generated answer + sources |
| GET | `/chat/history` | View past Q&A exchanges |
| GET | `/health` | Health check (server + database connectivity) |

Full interactive API documentation is available at `/docs` once the backend is running.

## Design decisions worth noting

- **Local embeddings over OpenAI**: swapped to `sentence-transformers` (free, runs locally) instead of OpenAI's embedding API, avoiding both cost and an external dependency for that step, while keeping the same architecture.
- **Groq over OpenAI for generation**: Groq offers a free tier with an OpenAI-compatible interface, keeping the LLM swap trivial if a different provider is preferred later.
- **Duplicate upload protection**: re-uploading a filename that already exists returns a `409 Conflict` rather than silently creating duplicate vector entries.
- **Input hardening**: file size limits, filename sanitization, corrupted/encrypted PDF detection, and question length limits — the app fails predictably rather than crashing on bad input.

## Possible extensions

- PostgreSQL instead of SQLite for the relational store
- Streaming responses (token-by-token) instead of waiting for the full answer
- Multi-user auth
- Support for additional file types (CSV, DOCX)
