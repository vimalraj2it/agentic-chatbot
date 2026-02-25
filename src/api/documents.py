from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from src.models.schemas import DocumentInfo, DocumentListResponse, DocumentUpdateResponse
from src.services.document_service import document_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """Lists all documents and their status"""
    docs = await document_service.list_documents()
    return DocumentListResponse(
        documents=[
            DocumentInfo(
                id=d["id"],
                filename=d["filename"],
                status=d["status"],
                updated_at=d["updated_at"]
            ) for d in docs
        ]
    )

@router.post("/upload", response_model=DocumentUpdateResponse)
async def upload_document(file: UploadFile = File(...)):
    """Uploads a new PDF document"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        doc_id = await document_service.upload_document(file)
        return DocumentUpdateResponse(
            success=True,
            message=f"Document {file.filename} uploaded successfully",
            status="unloaded"
        )
    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))

@router.post("/{doc_id}/load", response_model=DocumentUpdateResponse)
async def load_document(doc_id: str):
    """Indexes a document in FAISS"""
    try:
        await document_service.load_document(doc_id)
        return DocumentUpdateResponse(success=True, message="Document indexed successfully", status="loaded")
    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))

@router.post("/{doc_id}/unload", response_model=DocumentUpdateResponse)
async def unload_document(doc_id: str):
    """Removes a document from FAISS index"""
    try:
        await document_service.unload_document(doc_id)
        return DocumentUpdateResponse(success=True, message="Document unloaded successfully", status="unloaded")
    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))

@router.post("/{doc_id}/reload", response_model=DocumentUpdateResponse)
async def reload_document(doc_id: str):
    """Reloads a document index (unload then load)"""
    try:
        await document_service.unload_document(doc_id)
        await document_service.load_document(doc_id)
        return DocumentUpdateResponse(success=True, message="Document re-indexed successfully", status="loaded")
    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))

@router.delete("/{doc_id}", response_model=DocumentUpdateResponse)
async def delete_document(doc_id: str):
    """Deletes document from FAISS, disk, and DB"""
    try:
        await document_service.delete_document(doc_id)
        return DocumentUpdateResponse(success=True, message="Document deleted successfully")
    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))
