from pydantic import BaseModel
from typing import Optional, List


class IngestTextRequest(BaseModel):
    text: str
    uri: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    k: int = 5


class QARequest(BaseModel):
    question: str
    k: int = 5
    use_openai: bool = False


class CompletenessRequest(BaseModel):
    query: str
    k: int = 20


class SearchResult(BaseModel):
    content: str
    score: float
    document_id: int
    uri: Optional[str]
    chunk_index: int
