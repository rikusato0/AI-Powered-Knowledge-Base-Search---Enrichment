import re
from typing import Iterable, List


_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def estimate_tokens(text: str) -> int:
    # Lightweight tokens approximation
    return max(1, len(text.split()))


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        return [text]
    text = clean_text(text)
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    n = len(text)
    step = max(1, chunk_size - overlap)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start += step
    return chunks
