"""Unit tests for GPT-Lab model registry sync helpers and service."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.models.compliance_model import ComplianceModel
from app.services.gptlab_model_sync_service import (
    GptLabModelSyncService,
    farm_name_from_api_base,
    is_chat_model,
    ollama_id_to_code,
)


def test_ollama_id_to_code():
    assert ollama_id_to_code("llama3.1:8b") == "GPTLAB_LLAMA3_1_8B"
    assert ollama_id_to_code("qwen3.5:9b") == "GPTLAB_QWEN3_5_9B"


def test_is_chat_model_filters_embeddings():
    assert is_chat_model("llama3.1:8b") is True
    assert is_chat_model("nomic-embed-text:latest") is False
    assert is_chat_model("mxbai-embed-large") is False


def test_farm_name_from_api_base():
    base = "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1"
    assert farm_name_from_api_base(base) == "GPU-farmi-004"


@pytest.mark.asyncio
async def test_sync_creates_and_skips_embeddings():
    from app.core.config import Settings

    settings = Settings(
        jwt_secret_key="test-secret",
        gptlab_api_key="test-key",
        gptlab_api_base="https://example.test/GPT-Lab/resources/GPU-farmi-004/v1",
    )
    db = AsyncMock()
    service = GptLabModelSyncService(db, settings=settings)
    service.models = AsyncMock()
    service.models.get_by_code.return_value = None
    service.models.list_by_code_prefix.return_value = []
    service.audit = AsyncMock()

    with patch.object(
        GptLabModelSyncService,
        "_build_model_payload",
        wraps=GptLabModelSyncService._build_model_payload,
    ):
        with patch(
            "app.services.gptlab_model_sync_service.GptLabClient.fetch_model_ids",
            new=AsyncMock(
                return_value=["llama3.1:8b", "nomic-embed-text:latest", "qwen3.5:9b"]
            ),
        ):
            result = await service.sync(actor_user_id=uuid.uuid4())

    assert result.created == 2
    assert result.updated == 0
    assert result.skipped == ["nomic-embed-text:latest"]
    assert result.models_synced == ["llama3.1:8b", "qwen3.5:9b"]
    assert service.models.create.await_count == 2


@pytest.mark.asyncio
async def test_sync_requires_api_key():
    from app.core.config import Settings

    settings = Settings(jwt_secret_key="test-secret", gptlab_api_key="")
    service = GptLabModelSyncService(AsyncMock(), settings=settings)

    with pytest.raises(HTTPException) as exc:
        await service.sync()

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_sync_updates_existing_without_changing_approval():
    from app.core.config import Settings

    settings = Settings(
        jwt_secret_key="test-secret",
        gptlab_api_key="test-key",
    )
    db = AsyncMock()
    service = GptLabModelSyncService(db, settings=settings)
    service.models = AsyncMock()
    service.audit = AsyncMock()

    existing = ComplianceModel(
        id=uuid.uuid4(),
        code="GPTLAB_LLAMA3_1_8B",
        name="Old name",
        provider="GPT-Lab (TUNI)",
        model_type="open_source",
        endpoint_url="https://old.example/v1",
        data_retention_policy="old",
        logging_enabled=False,
        data_leaves_platform=True,
        is_approved=False,
        is_active=True,
        metadata_json={"source": "gptlab"},
    )
    service.models.get_by_code.return_value = existing
    service.models.list_by_code_prefix.return_value = [existing]

    with patch(
        "app.services.gptlab_model_sync_service.GptLabClient.fetch_model_ids",
        new=AsyncMock(return_value=["llama3.1:8b"]),
    ):
        result = await service.sync(actor_user_id=uuid.uuid4())

    assert result.created == 0
    assert result.updated == 1
    assert existing.is_approved is False
    assert existing.name.startswith("GPT-Lab llama3.1:8b")
