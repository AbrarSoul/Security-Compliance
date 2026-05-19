from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.file import File
from app.models.file_metadata import FileMetadata


class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        file_id: UUID,
        user_id: UUID,
        original_name: str,
        storage_key: str,
        content_type: str | None,
        file_type: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> File:
        record = File(
            id=file_id,
            user_id=user_id,
            original_name=original_name,
            storage_key=storage_key,
            content_type=content_type,
            file_type=file_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            status="uploaded",
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def add_metadata(self, metadata: FileMetadata) -> FileMetadata:
        self.db.add(metadata)
        await self.db.flush()
        return metadata

    async def get_by_id(self, file_id: UUID) -> File | None:
        result = await self.db.execute(
            select(File)
            .options(selectinload(File.metadata_row))
            .where(File.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, file_id: UUID, user_id: UUID) -> File | None:
        result = await self.db.execute(
            select(File)
            .options(selectinload(File.metadata_row))
            .where(File.id == file_id, File.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[File]:
        result = await self.db.execute(
            select(File)
            .options(selectinload(File.metadata_row))
            .where(File.user_id == user_id)
            .order_by(File.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, file_record: File) -> None:
        await self.db.delete(file_record)
