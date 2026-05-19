from abc import ABC, abstractmethod
from uuid import UUID


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, storage_key: str, content: bytes) -> str:
        """Persist bytes and return the storage key."""

    @abstractmethod
    async def read(self, storage_key: str) -> bytes:
        """Read file content by storage key."""

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """Remove a stored object."""

    @abstractmethod
    def build_storage_key(self, user_id: UUID, file_id: UUID, extension: str) -> str:
        """Build a safe, non-user-controlled storage path."""

    def build_report_storage_key(self, user_id: UUID, report_id: UUID, extension: str) -> str:
        """Build storage path for generated reports."""
        ext = extension.lower().lstrip(".")
        return f"{user_id}/reports/{report_id}.{ext}"
