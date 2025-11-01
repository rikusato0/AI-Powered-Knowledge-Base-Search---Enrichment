from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.api.schemas import QARequest, CompletenessRequest
from app.application.services.qa_service import answer_question_and_citations, completeness_check

router = APIRouter(tags=["qa"])


@router.post("/qa")
def qa(req: QARequest):
    try:
        payload = answer_question_and_citations(
            question=req.question, top_k=req.k or settings.TOP_K_DEFAULT, use_openai=req.use_openai
        )
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/completeness")
def completeness(req: CompletenessRequest) -> dict:
    try:
        result = completeness_check(query=req.query, top_k=req.k or settings.TOP_K_DEFAULT)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
