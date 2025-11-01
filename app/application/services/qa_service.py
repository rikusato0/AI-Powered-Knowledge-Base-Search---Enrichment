from typing import Dict, Any, List
import os

import numpy as np  

from app.core.config import settings
from app.infrastructure.embeddings.sentence_transformer_provider import embed_query
from app.infrastructure.vectorstore.faiss_index import VectorIndex

try:
    from openai import OpenAI  
except Exception:
    OpenAI = None  


def _format_citations(chunks: List[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        uri = c.get("uri") or f"doc-{c.get('document_id')}"
        snippet = c.get("content", "").strip().replace("\n", " ")
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        lines.append(f"[{i}] ({uri}) {snippet}")
    return "\n".join(lines)


def answer_question_and_citations(*, question: str, top_k: int, use_openai: bool = False) -> Dict[str, Any]:
    q_vec = embed_query(question)
    chunks = VectorIndex.search(q_vec, top_k)
    if use_openai and settings.OPENAI_API_KEY and OpenAI is not None:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        context = _format_citations(chunks)
        prompt = (
            "You are a helpful assistant. Answer the user's question using ONLY the context provided.\n"
            "If the answer cannot be found in the context, say you don't know.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            answer = completion.choices[0].message.content or ""
        except Exception as e:
            answer = f"Retrieval-only fallback due to LLM error: {e}\n\n" + _format_citations(chunks)
    else:
        answer = "Retrieval-only mode. Provide your own synthesis using these snippets:\n\n" + _format_citations(chunks)
    return {"answer": answer, "citations": chunks}


def completeness_check(*, query: str, top_k: int) -> Dict[str, Any]:
    q_vec = embed_query(query)
    chunks = VectorIndex.search(q_vec, top_k)
    scores = [c.get("score", 0.0) for c in chunks]
    coverage = float(sum(scores) / max(1, len(scores))) if scores else 0.0
    is_complete = coverage >= 0.4
    return {"is_complete": is_complete, "coverage": coverage, "k": top_k, "results": chunks}
