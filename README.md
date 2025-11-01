AI-Powered Knowledge Base Search & Enrichment (Challenge 2)

Overview

This repository contains a working prototype of a document ingestion and semantic search system with Q&A and completeness checking APIs. It focuses on simplicity and reliability for a 24-hour deliverable while leaving clear extension points for scale and features.

Key Features

- Document ingestion for raw text and PDF (stores raw text and vector embeddings)
- Sentence-transformer embeddings (local, CPU-friendly) with FAISS vector index (persistent)
- Semantic search API returning ranked chunks with metadata
- Q&A API (RAG) with optional OpenAI integration; retrieval-only fallback
- Completeness check API estimating corpus coverage of a query
- Incremental updates using content SHA-256 to avoid redundant re-indexing
- Modular architecture for future tools (parsers, LLMs, stores)

Quickstart

1) Environment

- Python 3.10+ is recommended
- Windows, macOS, Linux supported (Windows tested)

2) Install

```bash
python -m venv .venv
. .venv/Scripts/activate  
pip install -r requirements.txt
```

3) Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Try the APIs

- Open Swagger UI: http://localhost:8000/docs

Examples (HTTP):

```bash
curl -X POST http://localhost:8000/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text":"This is a sample document about machine learning.", "uri":"sample-1"}'

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What is machine learning?", "k":5}'

curl -X POST http://localhost:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"question":"What is machine learning?", "k":5}'

curl -X POST http://localhost:8000/completeness \
  -H "Content-Type: application/json" \
  -d '{"query":"Neural networks overview", "k":10}'
```

Design Decisions & Trade-offs

- Embeddings: `all-MiniLM-L6-v2` (384-dim) for speed/size on CPU.
- Vector store: FAISS (inner product with cosine normalization) persisted to disk.
- DB: SQLite for simplicity; holds documents and chunks for metadata and re-indexing.
- Incremental updates: content hash (SHA-256). If unchanged, indexing is skipped.
- Parsers: PDF via `pypdf`; raw text via API. HTML/Docx can be added with new parsers.
- Q&A: Optional OpenAI integration for answer synthesis; otherwise returns retrieved context plus a note.

24-hour Constraints & Specific Trade-offs

- Scope: Retrieval-first system with optional LLM answer synthesis; no advanced reranking.
- Completeness metric: Simple similarity-based heuristic (avg score) vs. richer coverage metrics.
- Infra: Single-process FastAPI; no background job queue. For scale, add Celery/RQ workers.
- Storage: SQLite + FAISS for fast local prototyping; swap to Postgres+pgvector or a managed vector DB for large corpora.
- Parsing: Basic text/PDF support only; HTML/DOCX and OCR are out of scope for this iteration.
- Observability: Minimal logging; no tracing/metrics dashboards. Add OpenTelemetry in next phase.
- Security: No auth/rate limiting. Intended for local demo. In production, put behind gateway and add auth.
- Testing: Manual and Swagger-driven smoke tests; unit/integration tests not included due to time.

Scaling Considerations

- Swap SQLite+FAISS to Postgres+pgvector or a cloud vector DB for larger scale.
- Add distributed workers for ingestion and background batching.
- Stream chunking and embedding in batches to keep memory stable (already supported).
- Use async queues and backpressure for very large corpora.

Project Structure

```
app/
  main.py              # FastAPI app and routes
  config.py            # Settings and constants
  db.py                # SQLAlchemy engine/session
  models.py            # ORM models
  schemas.py           # Pydantic request/response models
  embeddings.py        # Sentence-transformer loader and wrappers
  vectorstore.py       # FAISS index manager (persistent)
  ingestion.py         # Pipeline: parse, chunk, hash, embed, index
  qa.py                # RAG-style Q&A and completeness helpers
  utils/
    text.py            # Cleaning and chunking
    pdf.py             # PDF extraction
data/
  (created at runtime for DB and index persistence)
```

How to Test

- Use Swagger UI to try endpoints interactively
- Use the sample curl commands above
- Re-ingest the same content to see `"status":"skipped"` (incremental updates)
- Change content for the same `uri` to see replacement (old vectors removed)
- Ingest a PDF via `/ingest/file` and then query `/search` and `/qa`
- Restart the server and run search again to confirm persistence under `data/`

Demo

- Record a <5 min screen capture showing: start server → ingest text → search → QA (retrieval-only and with OpenAI if set) → ingest PDF → completeness → restart and confirm persistence.

Deliverables Checklist

- Working prototype (local): yes
- README with design decisions, 24h trade-offs, run/test steps: yes
- Short Loom/screen recording demo: 
- Code in a GitHub repo: https://github.com/RikuSato0/AI-Powered-Knowledge-Base-Search---Enrichment


