"""
Table definitions for our structured data.

Note what does NOT live here: the actual PDF text content and its
vector embeddings. Those go into ChromaDB (added on Day 3) because
they need similarity search, which a relational database like this
one isn't built for. This file only stores structured metadata:
who uploaded what, and the conversation history.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    # Where the raw uploaded file lives on disk
    filepath = Column(String, nullable=False)
    # Filled in once Day 2/3 processing (text extraction + chunking) succeeds
    status = Column(String, default="uploaded")  # uploaded -> processing -> ready -> failed
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="documents")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    # Which document chunks the answer was grounded in (filled in Day 6)
    source_documents = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
