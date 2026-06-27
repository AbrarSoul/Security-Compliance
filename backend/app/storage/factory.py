from functools import lru_cache
import logging
from pathlib import Path

from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend

settings = get_settings()
logger = logging.getLogger(__name__)

_FALLBACK_STORAGE_PATH = "/tmp/compliance-uploads"


def _resolve_writable_storage_path(configured: str) -> Path:
    """Pick the first configured path that can be created and written on this host."""
    seen: set[Path] = set()
    candidates = [configured]
    if Path(configured).expanduser().resolve() != Path(_FALLBACK_STORAGE_PATH).resolve():
        candidates.append(_FALLBACK_STORAGE_PATH)

    for candidate in candidates:
        path = Path(candidate).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_bytes(b"")
            probe.unlink(missing_ok=True)
            if candidate != configured:
                logger.warning(
                    "Storage path %s is not writable; using %s",
                    configured,
                    path,
                )
            return path
        except OSError:
            continue
    raise ValueError(
        f"No writable storage path (tried {configured!r} and {_FALLBACK_STORAGE_PATH!r})"
    )


@lru_cache
def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "local":
        base_path = _resolve_writable_storage_path(settings.storage_local_path)
        return LocalStorageBackend(base_path=str(base_path))
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
