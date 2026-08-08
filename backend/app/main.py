"""
FastAPI application entrypoint.

Run with:  uvicorn app.main:app --reload
Then visit http://127.0.0.1:8000/docs to see the interactive API docs
that FastAPI generates automatically for you.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
from app import models  # noqa: F401  (import registers the models with Base)
from app.routes import documents, chat

# Creates the SQLite tables (users, documents, chat_history) on startup
# if they don't already exist. In a production system you'd use a
# migration tool (Alembic) instead of doing this directly, but this
# is the right level of complexity for Day 1.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise AI Knowledge Base (RAG)")

# Allows the React frontend (running on a different port, localhost:5173)
# to call this API. Without this, the browser blocks the requests as a
# security measure (CORS = Cross-Origin Resource Sharing).
app.add_middleware(
    CORSMiddleware,
      allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registers every endpoint defined in app/routes/documents.py
# (currently /upload and /documents) onto the main app.
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Confirms two things at once: the API process is alive, AND it can
    successfully talk to the database. Hit this at
    http://127.0.0.1:8000/health after starting the server.
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/")
def root():
    return {"message": "RAG Knowledge Base API — see /docs for endpoints"}
