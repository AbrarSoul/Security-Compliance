import hashlib
import uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.models.file_metadata import FileMetadata
from app.repositories.file_repository import FileRepository
from app.services.audit_service import AuditService
from app.services.files.metadata_extractor import extract_metadata
from app.services.files.validator import validate_upload
from app.storage.base import StorageBackend


class FileService:
    def __init__(self, db: AsyncSession, storage: StorageBackend):
        self.db = db
        self.storage = storage
        self.files = FileRepository(db)
        self.audit = AuditService(db)

    async def upload(self, user_id: UUID, upload: UploadFile):
        validated = await validate_upload(upload)
        file_id = uuid.uuid4()
        storage_key = self.storage.build_storage_key(user_id, file_id, validated.extension)
        checksum = hashlib.sha256(validated.content).hexdigest()

        try:
            await self.storage.save(storage_key, validated.content)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store file",
            ) from exc

        file_record = await self.files.create(
            file_id=file_id,
            user_id=user_id,
            original_name=validated.sanitized_name,
            storage_key=storage_key,
            content_type=upload.content_type,
            file_type=validated.file_type,
            size_bytes=len(validated.content),
            checksum_sha256=checksum,
        )

        extracted = extract_metadata(validated.file_type, validated.content)
        metadata = FileMetadata(
            file_id=file_record.id,
            row_count=extracted.row_count,
            column_count=extracted.column_count,
            schema_json=extracted.schema_json,
            preview_json=extracted.preview_json,
            extra_json=extracted.extra_json,
        )
        await self.files.add_metadata(metadata)
        await self.db.refresh(file_record, attribute_names=["metadata_row"])
        await self.audit.log(
            AuditAction.FILE_UPLOADED,
            user_id=user_id,
            resource_type="file",
            resource_id=file_record.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={
                "original_name": file_record.original_name,
                "file_type": file_record.file_type,
                "size_bytes": file_record.size_bytes,
            },
        )
        return file_record

    async def get_file(self, file_id: UUID, user_id: UUID):
        file_record = await self.files.get_by_id_for_user(file_id, user_id)
        if file_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return file_record

    async def list_files(self, user_id: UUID, limit: int = 50, offset: int = 0):
        return await self.files.list_by_user(user_id, limit=limit, offset=offset)

    async def delete_file(self, file_id: UUID, user_id: UUID) -> None:
        file_record = await self.get_file(file_id, user_id)
        try:
            await self.storage.delete(file_record.storage_key)
        except FileNotFoundError:
            pass
        await self.files.delete(file_record)
        await self.audit.log(
            AuditAction.FILE_DELETED,
            user_id=user_id,
            resource_type="file",
            resource_id=file_id,
            severity=audit_severity.INFO,
            status="success",
            metadata={"original_name": file_record.original_name},
        )
