import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from plugins.drive.service import drive_service
from .schemas import N8NFileResponse
from .models import DriveFile
from core.database import get_async_db

router = APIRouter(tags=["Google Drive"])

@router.post("/upload")
async def upload_image_to_drive(file: UploadFile = File(...), context: str = "drive", db = Depends(get_async_db)):
    """
    Endpoint to save images by sending them to an n8n webhook.
    """
    if not drive_service.service:
        raise HTTPException(
            status_code=500, 
            detail="N8N Drive plugin is not configured or failed to load. Please check credentials."
        )
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File content is required")
        mime_type = file.content_type or "image/jpeg"
        
        # We use asyncio.to_thread because upload_image contains blocking I/O calls
        result = await asyncio.to_thread(
            drive_service.upload_image, 
            file.filename, 
            content, 
            mime_type
        )

        n8n_file_response = N8NFileResponse(**result)

        drive_file = await (DriveFile(
            context=context,
            name=n8n_file_response.originalFilename,
            url=n8n_file_response.webContentLink,
            id_file=n8n_file_response.id,
            size=n8n_file_response.size,
            mime_type=n8n_file_response.mimeType
        ).save(db))



        return {
            "status": "success", 
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
