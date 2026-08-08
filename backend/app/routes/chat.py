"""
The chat endpoint — where the user actually asks questions and gets
real generated answers, grounded in their uploaded documents.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import ChatHistory, Document
from app.rag_chain import answer_question

router = APIRouter()

MAX_QUESTION_LENGTH = 1000  # generous for a real question, blocks accidental essay-length input


class ChatRequest(BaseModel):
    question: str
    document_id: int | None = None  # optional: restrict to one document (Day 7)


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if len(request.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Question is too long (max {MAX_QUESTION_LENGTH} characters).",
        )

    # Day 7: if a document_id was specified, confirm it actually exists
    # and is ready — otherwise give a clear error instead of a silent
    # empty result.
    if request.document_id is not None:
        doc = (
            db.query(Document)
            .filter(Document.id == request.document_id, Document.status == "ready")
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"No ready document found with id={request.document_id}.",
            )

    result = None
    try:
        result = answer_question(request.question, document_id=request.document_id)
    except Exception as e:
        # Covers LLM API failures: rate limits, network issues, invalid
        # API key, etc. We surface a clean message instead of a raw
        # traceback, but still let the person know something failed
        # rather than silently returning nothing.
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate an answer (the AI service may be unavailable): {str(e)}",
        )

    # Day 6: store this Q&A exchange in chat_history, so there's a
    # permanent record — useful for showing chat history in the
    # frontend later, and for debugging what the app answered and why.
    history_entry = ChatHistory(
        question=request.question,
        answer=result["answer"],
        source_documents=json.dumps(result["sources"]),
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return {
        "chat_id": history_entry.id,
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }


@router.get("/chat/history")
def get_chat_history(db: Session = Depends(get_db)):
    """Returns every past Q&A exchange, most recent first."""
    entries = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "question": e.question,
            "answer": e.answer,
            "sources": json.loads(e.source_documents) if e.source_documents else [],
            "created_at": e.created_at,
        }
        for e in entries
    ]
