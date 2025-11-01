import json
import os
import threading
from typing import List, Dict, Any

import faiss
import numpy as np

from app.core.config import settings
from app.core.db import SessionLocal
from app.infrastructure.persistence.models import Chunk, Document
from app.infrastructure.embeddings.sentence_transformer_provider import embed_texts


class VectorIndex:
    _index: faiss.Index | None = None
    _lock = threading.RLock()
    _dim: int | None = None

    @classmethod
    def initialize(cls, dimension: int) -> None:
        with cls._lock:
            cls._dim = dimension
            if os.path.exists(settings.INDEX_PATH):
                idx = faiss.read_index(settings.INDEX_PATH)
                if isinstance(idx, (faiss.IndexIDMap, faiss.IndexIDMap2)):
                    cls._index = idx
                else:
                    if idx.d != dimension:
                        cls._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))
                        cls._persist_meta()
                        cls._save()
                        cls._rebuild_from_db()
                    elif idx.ntotal == 0:
                        cls._index = faiss.IndexIDMap2(idx)
                        cls._persist_meta()
                        cls._save()
                    else:
                        cls._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))
                        cls._persist_meta()
                        cls._save()
                        cls._rebuild_from_db()
                if cls._index is not None and cls._index.d != dimension:
                    cls._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))
                    cls._persist_meta()
                    cls._save()
                    cls._rebuild_from_db()
            else:
                cls._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))
                cls._persist_meta()
                cls._save()

    @classmethod
    def _persist_meta(cls) -> None:
        meta = {"dimension": cls._dim, "model": settings.MODEL_NAME}
        os.makedirs(os.path.dirname(settings.INDEX_META_PATH), exist_ok=True)
        with open(settings.INDEX_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f)

    @classmethod
    def _save(cls) -> None:
        assert cls._index is not None
        faiss.write_index(cls._index, settings.INDEX_PATH)

    @classmethod
    def _rebuild_from_db(cls, batch_size: int = 256) -> None:
        assert cls._index is not None
        last_id = 0
        with SessionLocal() as session:
            while True:
                rows: List[Chunk] = (
                    session.query(Chunk)
                    .filter(Chunk.id > last_id)
                    .order_by(Chunk.id.asc())
                    .limit(batch_size)
                    .all()
                )
                if not rows:
                    break
                texts = [r.content for r in rows]
                ids = [int(r.id) for r in rows]
                vectors = embed_texts(texts)
                cls._index.add_with_ids(vectors, np.array(ids, dtype=np.int64))
                last_id = rows[-1].id
        cls._save()

    @classmethod
    def add(cls, embeddings: np.ndarray, ids: List[int]) -> None:
        assert cls._index is not None
        with cls._lock:
            cls._index.add_with_ids(embeddings, np.array(ids, dtype=np.int64))
            cls._save()

    @classmethod
    def remove_ids(cls, ids: List[int]) -> None:
        assert cls._index is not None
        if not ids:
            return
        with cls._lock:
            to_remove = faiss.IDSelectorArray(np.array(ids, dtype=np.int64))
            cls._index.remove_ids(to_remove)
            cls._save()

    @classmethod
    def search(cls, query_vec: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        assert cls._index is not None
        with cls._lock:
            distances, id_matrix = cls._index.search(query_vec, top_k)
        id_list = id_matrix[0].tolist()
        score_list = distances[0].tolist()
        results: List[Dict[str, Any]] = []
        with SessionLocal() as session:
            rows = (
                session.query(Chunk, Document)
                .join(Document, Chunk.document_id == Document.id)
                .filter(Chunk.id.in_([cid for cid in id_list if cid != -1]))
                .all()
            )
            chunk_by_id = {chunk.id: (chunk, doc) for (chunk, doc) in rows}
        for cid, score in zip(id_list, score_list):
            if cid == -1:
                continue
            pair = chunk_by_id.get(cid)
            if not pair:
                continue
            chunk, doc = pair
            results.append(
                {
                    "content": chunk.content,
                    "score": float(score),
                    "document_id": int(doc.id),
                    "uri": doc.uri,
                    "chunk_index": int(chunk.chunk_index),
                }
            )
        return results
