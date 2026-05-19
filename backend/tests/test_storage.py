import uuid

import pytest

from app.storage.local import LocalStorageBackend


@pytest.fixture
def storage(tmp_path):
    return LocalStorageBackend(base_path=str(tmp_path))


@pytest.mark.asyncio
async def test_local_storage_save_read_delete(storage):
    user_id = uuid.uuid4()
    file_id = uuid.uuid4()
    key = storage.build_storage_key(user_id, file_id, "csv")
    content = b"col1,col2\n1,2\n"

    await storage.save(key, content)
    assert await storage.read(key) == content
    await storage.delete(key)

    with pytest.raises(FileNotFoundError):
        await storage.read(key)


def test_storage_rejects_path_traversal(storage):
    with pytest.raises(ValueError, match="Invalid storage key"):
        storage._resolve_path("..\\etc/passwd")


@pytest.mark.asyncio
async def test_report_storage_key(storage):
    user_id = uuid.uuid4()
    report_id = uuid.uuid4()
    key = storage.build_report_storage_key(user_id, report_id, "pdf")
    content = b"%PDF-test"
    await storage.save(key, content)
    assert await storage.read(key) == content
    await storage.delete(key)
