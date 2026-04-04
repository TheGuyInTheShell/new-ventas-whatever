from typing import List, Optional
from pydantic import BaseModel


class N8NPermission(BaseModel):
    kind: str
    id: str
    type: str
    emailAddress: str
    role: str
    displayName: str
    deleted: bool
    pendingOwner: bool

class N8NImageMediaMetadata(BaseModel):
    width: int
    height: int
    rotation: int

class N8NLinkShareMetadata(BaseModel):
    securityUpdateEligible: bool
    securityUpdateEnabled: bool

class N8NFileResponse(BaseModel):
    id: str
    canShare: Optional[bool] = None
    canTrash: Optional[bool] = None
    canUntrash: Optional[bool] = None
    webContentLink: Optional[str] = None
    mimeType: str
    viewersCanCopyContent: Optional[bool] = None
    copyRequiresWriterPermission: Optional[bool] = None
    writersCanShare: Optional[bool] = None
    permissions: Optional[List[N8NPermission]] = None
    permissionIds: Optional[List[str]] = None
    originalFilename: str
    fullFileExtension: Optional[str] = None
    fileExtension: Optional[str] = None
    md5Checksum: Optional[str] = None
    sha1Checksum: Optional[str] = None
    sha256Checksum: Optional[str] = None
    size: str
    quotaBytesUsed: Optional[str] = None
    headRevisionId: Optional[str] = None
    imageMediaMetadata: Optional[N8NImageMediaMetadata] = None
    isAppAuthorized: Optional[bool] = None
    linkShareMetadata: Optional[N8NLinkShareMetadata] = None
    inheritedPermissionsDisabled: Optional[bool] = None


class DriveFileBase(BaseModel):
    context: str
    name: str
    url: str
    id_file: str
    size: str
    mime_type: str


