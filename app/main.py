from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import Base, engine
from app.infrastructure.embeddings.sentence_transformer_provider import get_embedding_dimension
from app.infrastructure.vectorstore.faiss_index import VectorIndex

from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.search import router as search_router
from app.api.routes.qa import router as qa_router


app = FastAPI(title="Knowledge Base Search & Q&A", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    VectorIndex.initialize(dimension=get_embedding_dimension())


# Routers
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(search_router)
app.include_router(qa_router)
