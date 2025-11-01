import threading
from typing import List
import numpy as np  

from sentence_transformers import SentenceTransformer  

from app.core.config import settings

_model_lock = threading.Lock()
_model: SentenceTransformer | None = None
_dim: int | None = None


def _load_model() -> SentenceTransformer:
    global _model, _dim
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(settings.MODEL_NAME, device=settings.DEVICE)
                # Probe dimension
                probe = _model.encode(["dim"], convert_to_numpy=True, normalize_embeddings=False)
                _dim = probe.shape[1]
    return _model


def get_embedding_dimension() -> int:
    if _dim is None:
        _load_model()
    assert _dim is not None
    return _dim


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    return matrix / norms


def embed_texts(texts: List[str]) -> np.ndarray:
    model = _load_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
    vectors = _normalize(vectors)
    return vectors.astype(np.float32)


def embed_query(text: str) -> np.ndarray:
    vec = embed_texts([text])
    return vec
