from fastapi import APIRouter, UploadFile, File, HTTPException

from app.api.schemas import IngestTextRequest
from app.application.services.ingestion_service import ingest_text_document, ingest_file_document

router = APIRouter(tags=["ingest"])


@router.post("/ingest/text")
def ingest_text(req: IngestTextRequest) -> dict:
    try:
        result = ingest_text_document(text=req.text, uri=req.uri)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)) -> dict:
    try:
        result = await ingest_file_document(file)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
