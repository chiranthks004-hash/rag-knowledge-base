"""
Database connection setup.

For now we use SQLite (a single local file, zero setup needed).
Later, when Docker is installed, we swap DATABASE_URL to point at
PostgreSQL — the rest of the code (models, queries) barely changes,
because SQLAlchemy abstracts the actual database engine away from us.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLite database file. DATA_DIR defaults to the current folder for
# local development, but in Docker we point it at /app/data, which is
# a mounted volume — so the database survives container restarts
# instead of disappearing when the container is recreated.
DATA_DIR = os.getenv("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR}/app.db"

# check_same_thread=False is an SQLite-specific quirk required to let
# FastAPI (which is async/multi-threaded) talk to a SQLite file safely.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our table models will inherit from this Base class.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: gives each request its own database session,
    and guarantees it's closed afterward even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
