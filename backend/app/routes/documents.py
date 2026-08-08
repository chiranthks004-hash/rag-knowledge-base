"""
Endpoint for uploading a PDF and extracting its raw text.

Day 8 hardening added: file size limits, empty-file detection,
filename sanitization, and cleanup of partial files on failure —
so a bad upload fails cleanly instead of leaving orphaned files
or a half-broken document record behind.
"""

import os
import re
import shutil

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.database import get_db
from app.models import Document
from app.text_processing import chunk_text
from app.vector_store import vector_store
from langchain.schema import Document as LangchainDocument

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploaded_files"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB — generous for text PDFs, blocks accidental huge uploads


def sanitize_filename(filename: str) -> str:
    """
    Strips anything that isn't a normal filename character. Prevents
    a maliciously or accidentally crafted filename (e.g. containing
    '../') from writing outside the intended upload folder, and avoids
    filesystem issues with special characters.
    """
    base = os.path.basename(filename)  # drops any directory components
    return re.sub(r"[^A-Za-z0-9._ -]", "_", base)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), force: bool = False, db: Session = Depends(get_db)
):
    # Only accept PDFs for now — CSVs and other types come later
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now.")

    safe_filename = sanitize_filename(file.filename)
    if not safe_filename or safe_filename == ".pdf":
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Day 4: warn if this filename was already uploaded successfully before.
    existing = (
        db.query(Document)
        .filter(Document.filename == safe_filename, Document.status == "ready")
        .first()
    )
    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A document named '{safe_filename}' was already uploaded "
                f"(document_id={existing.id}). Re-uploading it will create duplicate "
                f"chunks in the vector store. If you're sure you want to proceed "
                f"(e.g. it's an updated version), resend the request with force=true."
            ),
        )

    # Step 1: save the uploaded file to disk, enforcing a size limit
    # as we go (rather than reading the whole thing into memory first,
    # which would let a huge file exhaust memory before we even get
    # to check its size).
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    total_bytes = 0
    CHUNK = 1024 * 1024  # read 1MB at a time
    with open(filepath, "wb") as buffer:
        while True:
            piece = await file.read(CHUNK)
            if not piece:
                break
            total_bytes += len(piece)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                buffer.close()
                os.remove(filepath)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)}MB upload limit.",
                )
            buffer.write(piece)

    if total_bytes == 0:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Step 2: record it in the database with status "processing"
    document = Document(filename=safe_filename, filepath=filepath, status="processing")
    db.add(document)
    db.commit()
    db.refresh(document)

    # Step 3: extract text from the PDF
    try:
        try:
            reader = PdfReader(filepath)
        except PdfReadError:
            raise HTTPException(
                status_code=422,
                detail="This file isn't a valid or readable PDF (it may be corrupted).",
            )

        if reader.is_encrypted:
            document.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=422,
                detail="This PDF is password-protected. Remove the password and try again.",
            )

        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() or ""

        if not extracted_text.strip():
            document.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in this PDF (it may be a scanned image).",
            )

        document.status = "ready"
        db.commit()

        # Step 3b: split the extracted text into chunks, and store each
        # chunk's embedding in ChromaDB.
        chunks = chunk_text(extracted_text)
        langchain_docs = [
            LangchainDocument(
                page_content=chunk,
                metadata={"document_id": document.id, "filename": document.filename},
            )
            for chunk in chunks
        ]
        vector_store.add_documents(langchain_docs)

    except HTTPException:
        # Clean up the saved file on disk if processing failed, so
        # failed uploads don't quietly pile up in uploaded_files/.
        if os.path.exists(filepath) and document.status != "ready":
            os.remove(filepath)
        raise
    except Exception as e:
        document.status = "failed"
        db.commit()
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    # Step 4: return proof it worked
    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "extracted_text_preview": extracted_text[:500],
        "total_characters_extracted": len(extracted_text),
        "num_chunks_created": len(chunks),
    }


@router.get("/search")
def search_documents(query: str, top_k: int = 3, db: Session = Depends(get_db)):
    """
    Given a plain-English query, returns the most semantically similar
    chunks stored in ChromaDB — no LLM involved yet, just proving the
    vector search itself works.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    ready_docs = db.query(Document).filter(Document.status == "ready").count()
    if ready_docs == 0:
        raise HTTPException(
            status_code=404,
            detail="No documents have been uploaded yet. Upload a PDF via /upload first.",
        )

    results = vector_store.similarity_search(query, k=top_k)
    return [
        {
            "content": r.page_content,
            "source_filename": r.metadata.get("filename"),
            "document_id": r.metadata.get("document_id"),
        }
        for r in results
    ]


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """Lists every document uploaded so far, with its status."""
    documents = db.query(Document).all()
    return [
        {"id": d.id, "filename": d.filename, "status": d.status, "created_at": d.created_at}
        for d in documents
    ]
