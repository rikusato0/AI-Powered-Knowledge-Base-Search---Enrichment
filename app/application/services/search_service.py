from typing import List, Dict, Any

from app.core.config import settings
from app.infrastructure.embeddings.sentence_transformer_provider import embed_query
from app.infrastructure.vectorstore.faiss_index import VectorIndex


def search_documents(query: str, top_k: int) -> List[Dict[str, Any]]:
    query_vec = embed_query(query)
    results = VectorIndex.search(query_vec=query_vec, top_k=top_k or settings.TOP_K_DEFAULT)
    return results
