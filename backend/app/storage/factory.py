from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend

settings = get_settings()


@lru_cache
def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorageBackend()
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
