from typing import List
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.api.schemas import SearchRequest, SearchResult
from app.application.services.search_service import search_documents

router = APIRouter(tags=["search"])


@router.post("/search", response_model=List[SearchResult])
def search(req: SearchRequest):
    try:
        return search_documents(query=req.query, top_k=req.k or settings.TOP_K_DEFAULT)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
