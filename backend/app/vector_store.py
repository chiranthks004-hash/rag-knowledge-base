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
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma

load_dotenv()  # reads the .env file (used later for the LLM API key)

CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_store"))
os.makedirs(CHROMA_DIR, exist_ok=True)

# fastembed runs on ONNX Runtime instead of full PyTorch — same idea as
# sentence-transformers (free, local, no API key), but with a much
# smaller memory footprint. This matters on memory-constrained hosts
# like Render's free tier (512MB), where PyTorch alone can exceed the limit.
embedding_function = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# This is our single collection of vectors, persisted to disk in
# chroma_store/ so it survives server restarts.
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embedding_function,
    persist_directory=CHROMA_DIR,
)