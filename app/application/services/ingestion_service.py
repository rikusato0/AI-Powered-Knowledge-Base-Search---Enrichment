import hashlib
import os
import tempfile
from typing import List, Tuple, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session  

from app.core.config import settings
from app.core.db import SessionLocal
from app.infrastructure.persistence.models import Document, Chunk
from app.infrastructure.text.text_utils import chunk_text, estimate_tokens, clean_text
from app.infrastructure.parsers.pdf_reader import extract_text_pages
from app.infrastructure.embeddings.sentence_transformer_provider import embed_texts
from app.infrastructure.vectorstore.faiss_index import VectorIndex


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _persist_document(session: Session, *, uri: Optional[str], source_type: str, sha256: str, num_chunks: int) -> Document:
    doc = Document(uri=uri, source_type=source_type, sha256=sha256, num_chunks=num_chunks)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def _persist_chunks(session: Session, document_id: int, chunks: List[str]) -> List[Chunk]:
    chunk_rows: List[Chunk] = []
    for idx, content in enumerate(chunks):
        row = Chunk(document_id=document_id, chunk_index=idx, content=content, token_count=estimate_tokens(content))
        session.add(row)
        chunk_rows.append(row)
    session.commit()
    for row in chunk_rows:
        session.refresh(row)
    return chunk_rows


def _index_chunks(chunks: List[Chunk]) -> None:
    texts = [c.content for c in chunks]
    vectors = embed_texts(texts)
    ids = [int(c.id) for c in chunks]
    VectorIndex.add(vectors, ids)


def _maybe_skip_existing(session: Session, sha256: str, uri: Optional[str]) -> Optional[Document]:
    existing = session.query(Document).filter(Document.sha256 == sha256).first()
    if existing is not None:
        return existing
    if uri:
        existing_uri = session.query(Document).filter(Document.uri == uri).first()
        if existing_uri is not None:
            old_chunk_ids = [c.id for c in existing_uri.chunks]
            VectorIndex.remove_ids(old_chunk_ids)
            session.delete(existing_uri)
            session.commit()
    return None


def _ingest_text_core(text: str, uri: Optional[str], source_type: str) -> dict:
    cleaned = clean_text(text)
    if not cleaned:
        return {"status": "empty", "num_chunks": 0}
    parts = chunk_text(cleaned, settings.CHUNK_SIZE_CHARS, settings.CHUNK_OVERLAP_CHARS)
    content_hash = _sha256_text(cleaned)
    with SessionLocal() as session:
        existing = _maybe_skip_existing(session, content_hash, uri)
        if existing is not None:
            return {"status": "skipped", "document_id": int(existing.id), "num_chunks": int(existing.num_chunks)}
        doc = _persist_document(session, uri=uri, source_type=source_type, sha256=content_hash, num_chunks=len(parts))
        chunk_rows = _persist_chunks(session, doc.id, parts)
        _index_chunks(chunk_rows)
        return {"status": "ingested", "document_id": int(doc.id), "num_chunks": len(parts)}


def ingest_text_document(*, text: str, uri: Optional[str] = None) -> dict:
    return _ingest_text_core(text=text, uri=uri, source_type="api")


async def ingest_file_document(file: UploadFile) -> dict:
    filename = file.filename or "uploaded"
    ext = os.path.splitext(filename.lower())[1]
    if ext not in [".txt", ".pdf"]:
        raise ValueError("Only .txt and .pdf are supported for this prototype")
    data = await file.read()
    if ext == ".txt":
        text = data.decode("utf-8", errors="ignore")
        return _ingest_text_core(text=text, uri=filename, source_type="file")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp.flush()
            temp_path = tmp.name
        try:
            pages = list(extract_text_pages(temp_path))
            combined = "\n\n".join(pages)
            return _ingest_text_core(text=combined, uri=filename, source_type="file")
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
