from typing import Optional
from pydantic import BaseModel


class ImgCDNImage(BaseModel):
    """Nested 'image' object from the imgcdn.dev API v1 response."""
    url: str
    url_viewer: Optional[str] = None
    size: int
    filename: str
    name: str
    mime: str
    extension: str
    width: Optional[int] = None
    height: Optional[int] = None


class ImgCDNResponse(BaseModel):
    """Top-level response from imgcdn.dev API v1 upload endpoint."""
    status_code: int
    status_txt: Optional[str] = None
    image: ImgCDNImage


class ImageFileBase(BaseModel):
    """Drive-compatible schema for database-level compatibility with DriveFileBase."""
    context: str
    name: str
    url: str
    id_file: str
    size: str
    mime_type: str
