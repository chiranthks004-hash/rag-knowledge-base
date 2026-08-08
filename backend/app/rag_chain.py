"""
The actual RAG (Retrieval-Augmented Generation) pipeline.

This is the piece that turns "search results" into "a real answer."
The flow:
  1. Take the user's question
  2. Retrieve the most relevant chunks from ChromaDB (same as Day 3's /search)
  3. Stuff those chunks into a prompt template, along with the question
  4. Send that combined prompt to the LLM (Groq, in our case)
  5. Return the generated answer, plus which chunks/documents it came from

Why this matters: the LLM never gets asked the question "cold." It's
only ever asked to answer USING the retrieved text — which is what
grounds the answer in your actual documents instead of the model's
general training knowledge, and is why RAG reduces hallucination.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

from app.vector_store import vector_store

load_dotenv()

# llama-3.1-8b-instant is Groq's fast, free-tier-friendly model —
# plenty capable for answering questions grounded in retrieved text.
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are a helpful assistant answering questions using ONLY the context provided below.
If the answer is not contained in the context, say "I don't have enough information in the
uploaded documents to answer that" rather than making something up.

Context:
{context}

Question: {question}

Answer:"""
)


def answer_question(question: str, top_k: int = 4, document_id: int | None = None) -> dict:
    """
    Runs the full RAG pipeline: retrieve relevant chunks, generate an
    answer grounded in them, and return the answer plus its sources.

    document_id: if provided, restricts retrieval to chunks from that
    one document only (built out fully on Day 7 for multi-doc filtering).
    """
    # Step 1: retrieve relevant chunks (optionally filtered to one document)
    filter_dict = {"document_id": document_id} if document_id is not None else None
    results = vector_store.similarity_search(question, k=top_k, filter=filter_dict)

    if not results:
        return {
            "answer": "I don't have enough information in the uploaded documents to answer that.",
            "sources": [],
        }

    # Step 2: combine the retrieved chunks into one context block
    context = "\n\n---\n\n".join(r.page_content for r in results)

    # Step 3: fill the prompt template and call the LLM
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    response = llm.invoke(prompt)

    # Step 4: build a clean, de-duplicated list of sources
    sources = []
    seen = set()
    for r in results:
        key = (r.metadata.get("document_id"), r.metadata.get("filename"))
        if key not in seen:
            seen.add(key)
            sources.append({"document_id": key[0], "filename": key[1]})

    return {"answer": response.content, "sources": sources}
