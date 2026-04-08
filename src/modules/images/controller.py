import asyncio
import requests
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from core.config.settings import settings
from .schemas import ImgCDNResponse
from .models import ImageFile
from core.database import get_async_db

router = APIRouter(tags=["Images"])

IMGCDN_UPLOAD_URL = "https://imgcdn.dev/api/1/upload"


def _upload_to_imgcdn(file_content: bytes, filename: str, api_key: str) -> dict:
    """Blocking upload to imgcdn.dev — meant to be called via asyncio.to_thread."""
    payload = {
        "key": api_key,
        "format": "json",
    }
    files = {
        "source": (filename, file_content),
    }
    response = requests.post(IMGCDN_UPLOAD_URL, data=payload, files=files)
    res_json = response.json()
    if response.status_code != 200:
        # Check if it was a duplicate upload (imgcdn.dev returns 400 with 'Duplicated upload' and still provides the image object)
        if response.status_code == 400 and res_json.get("error", {}).get("message") == "Duplicated upload":
            if "image" in res_json:
                return res_json
        raise Exception(f"imgcdn.dev returned status {response.status_code}: {response.text}")
    return res_json


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    context: str = "imgcdn",
    db=Depends(get_async_db),
):
    """
    Upload an image to imgcdn.dev and save the reference in the database.
    Returns a Drive-compatible response for frontend interoperability.
    """
    api_key = settings.IMGCDN_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="IMGCDN_API_KEY is not configured. Please set it in your .env file.",
        )

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File content is required")

        mime_type = file.content_type or "image/jpeg"

        # Blocking I/O — run in a thread
        result = await asyncio.to_thread(
            _upload_to_imgcdn, content, file.filename, api_key
        )

        imgcdn_response = ImgCDNResponse(**result)

        # Persist the reference in the database
        image_file = await ImageFile(
            context=context,
            name=imgcdn_response.image.filename,
            url=imgcdn_response.image.url,
            id_file=imgcdn_response.image.name,
            size=str(imgcdn_response.image.size),
            mime_type=imgcdn_response.image.mime or mime_type,
        ).save(db)

        return {
            "status": "success",
            "data": {
                "id_file": image_file.id_file,
                "name": image_file.name,
                "url": image_file.url,
                "size": image_file.size,
                "mime_type": image_file.mime_type,
                "context": image_file.context,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
