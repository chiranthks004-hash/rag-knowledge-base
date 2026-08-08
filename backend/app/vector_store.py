"""
Vector store setup.

This is the piece that makes your app "AI-powered" rather than just
a file storage app. Here's the concept in plain words:

- An "embedding" is a list of numbers (e.g., 1536 numbers) that
  represents the MEANING of a piece of text. Two chunks of text
  with similar meaning end up with similar numbers, even if they
  don't share any exact words.
- ChromaDB is a database built specifically to store these number-lists
  and quickly find "which stored chunks have numbers most similar to
  this new query" — that's what powers semantic search.

We load the OpenAI API key from the .env file (never hardcoded).
"""

import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()  # reads the .env file (still used later for the LLM call itself)

CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_store"))
os.makedirs(CHROMA_DIR, exist_ok=True)

# A free, local embedding model — runs on your own laptop, no API key
# or billing needed. "all-MiniLM-L6-v2" is small, fast, and widely
# used for exactly this kind of project. The first time this runs,
# it downloads the model (~80MB) once; after that it's cached locally.
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# This is our single collection of vectors, persisted to disk in
# chroma_store/ so it survives server restarts.
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embedding_function,
    persist_directory=CHROMA_DIR,
)
