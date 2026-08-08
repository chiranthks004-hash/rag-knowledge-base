"""
Splits extracted PDF text into smaller overlapping chunks.

Why chunk at all? LLMs and embeddings work better on small, focused
pieces of text rather than one giant blob. If someone asks a question,
we want to retrieve just the 2-3 relevant paragraphs, not dump an
entire 50-page PDF into the prompt every time.

Why OVERLAPPING chunks? If we cut text at hard boundaries, we risk
splitting a sentence or idea right down the middle, and losing it
from both chunks. A small overlap (chunk_overlap) means each chunk
shares a bit of text with its neighbor, so context isn't lost at
the seams.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # characters per chunk (roughly 150-200 words)
    chunk_overlap=150,     # how much each chunk overlaps with the next
    length_function=len,
)


def chunk_text(text: str) -> list[str]:
    """Takes raw extracted PDF text and returns a list of text chunks."""
    return text_splitter.split_text(text)
