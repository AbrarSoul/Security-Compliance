from pathlib import Path
from uuid import UUID

import aiofiles

from app.core.config import get_settings
from app.storage.base import StorageBackend

settings = get_settings()


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.storage_local_path).resolve()

    def build_storage_key(self, user_id: UUID, file_id: UUID, extension: str) -> str:
        ext = extension.lower().lstrip(".")
        return f"{user_id}/{file_id}.{ext}"

    def build_report_storage_key(self, user_id: UUID, report_id: UUID, extension: str) -> str:
        ext = extension.lower().lstrip(".")
        return f"{user_id}/reports/{report_id}.{ext}"

    def _resolve_path(self, storage_key: str) -> Path:
        parts = storage_key.replace("\\", "/").split("/")
        if len(parts) not in (2, 3) or ".." in parts or any(not p for p in parts):
            raise ValueError("Invalid storage key")
        if not all(part.replace("-", "").replace(".", "").isalnum() for part in parts):
            raise ValueError("Invalid storage key")
        path = self.base_path
        for part in parts:
            path = path / part
        path = path.resolve()
        if not path.is_relative_to(self.base_path):
            raise ValueError("Path traversal detected")
        return path

    async def save(self, storage_key: str, content: bytes) -> str:
        path = self._resolve_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        return storage_key

    async def read(self, storage_key: str) -> bytes:
        path = self._resolve_path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(storage_key)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, storage_key: str) -> None:
        path = self._resolve_path(storage_key)
        if path.is_file():
            path.unlink()
