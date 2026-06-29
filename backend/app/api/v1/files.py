from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import FILE_READ, FILE_UPLOAD
from app.db.session import get_db
from app.schemas.files import (
    FileListResponse,
    FileMetadataResponse,
    FileResponse,
    FileUploadResponse,
)
from app.services.files.file_service import FileService
from app.storage import get_storage_backend

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    return FileService(db, get_storage_backend())


def _to_file_response(file_record) -> FileResponse:
    metadata = None
    if file_record.metadata_row:
        metadata = FileMetadataResponse.model_validate(file_record.metadata_row)
    return FileResponse(
        id=file_record.id,
        original_name=file_record.original_name,
        file_type=file_record.file_type,
        content_type=file_record.content_type,
        size_bytes=file_record.size_bytes,
        checksum_sha256=file_record.checksum_sha256,
        status=file_record.status,
        created_at=file_record.created_at,
        metadata=metadata,
    )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    ctx: AuthContext = Depends(require_permission(FILE_UPLOAD)),
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
):
    """Upload a supported dataset file. Extracts metadata automatically."""
    record = await file_service.upload(ctx.user.id, file)
    return FileUploadResponse(file=_to_file_response(record))


@router.get("", response_model=FileListResponse)
async def list_files(
    ctx: AuthContext = Depends(require_permission(FILE_READ)),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    file_service: FileService = Depends(get_file_service),
):
    """List uploaded files for the authenticated user."""
    items = await file_service.list_files(ctx.user.id, limit=limit, offset=offset)
    return FileListResponse(
        items=[_to_file_response(f) for f in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: UUID,
    ctx: AuthContext = Depends(require_permission(FILE_READ)),
    file_service: FileService = Depends(get_file_service),
):
    """Get file details and metadata."""
    record = await file_service.get_file(file_id, ctx.user.id)
    return _to_file_response(record)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    ctx: AuthContext = Depends(require_permission(FILE_READ)),
    file_service: FileService = Depends(get_file_service),
):
    """Delete file from storage and database."""
    await file_service.delete_file(file_id, ctx.user.id)
