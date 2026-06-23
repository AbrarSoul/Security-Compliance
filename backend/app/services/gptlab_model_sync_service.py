"""Sync GPT-Lab Ollama models into the compliance model registry."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.compliance_model import ComplianceModel
from app.repositories.compliance_model_repository import ComplianceModelRepository
from app.services.audit_service import AuditService
from app.services.llm.gptlab_client import GptLabClient, GptLabClientError

GPTLAB_CODE_PREFIX = "GPTLAB_"
GPTLAB_METADATA_SOURCE = "gptlab"
DEMO_MODEL_CODES = frozenset(
    {"DEMO_LOCAL_LLM", "DEMO_EXTERNAL_API", "DEMO_CLOUD_UNAPPROVED"}
)
EMBED_HINTS = ("embed", "embedding", "nomic-embed")


@dataclass
class GptLabSyncResult:
    created: int = 0
    updated: int = 0
    deactivated: int = 0
    demos_deactivated: int = 0
    models_synced: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def ollama_id_to_code(ollama_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ollama_id).strip("_").upper()
    return f"{GPTLAB_CODE_PREFIX}{slug}"


def is_chat_model(model_id: str) -> bool:
    lower = model_id.lower()
    return not any(hint in lower for hint in EMBED_HINTS)


def farm_name_from_api_base(api_base: str) -> str:
    path = urlparse(api_base).path.strip("/")
    if not path:
        return "unknown"
    parts = [part for part in path.split("/") if part and part != "v1"]
    return parts[-1] if parts else "unknown"


def display_name(ollama_id: str, farm: str) -> str:
    return f"GPT-Lab {ollama_id} ({farm})"


class GptLabModelSyncService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.models = ComplianceModelRepository(db)
        self.audit = AuditService(db)

    async def sync(
        self,
        *,
        actor_user_id: UUID | None = None,
        approve_new: bool = True,
        deactivate_demos: bool = False,
        deactivate_missing: bool = True,
    ) -> GptLabSyncResult:
        api_key = self.settings.gptlab_api_key
        api_base = self.settings.gptlab_api_base
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPTLAB_API_KEY is not configured",
            )

        client = GptLabClient(api_base=api_base, api_key=api_key)
        try:
            remote_ids = await client.fetch_model_ids()
        except GptLabClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        farm = farm_name_from_api_base(api_base)
        result = GptLabSyncResult()
        seen_codes: set[str] = set()

        for ollama_id in remote_ids:
            if not is_chat_model(ollama_id):
                result.skipped.append(ollama_id)
                continue

            code = ollama_id_to_code(ollama_id)
            seen_codes.add(code)
            payload = self._build_model_payload(
                code=code,
                ollama_id=ollama_id,
                api_base=api_base,
                farm=farm,
                approve_new=approve_new,
            )

            existing = await self.models.get_by_code(code)
            if existing is None:
                model = ComplianceModel(
                    id=uuid.uuid4(),
                    code=payload["code"],
                    name=payload["name"],
                    provider=payload["provider"],
                    model_type=payload["model_type"],
                    endpoint_url=payload["endpoint_url"],
                    data_retention_policy=payload["data_retention_policy"],
                    logging_enabled=payload["logging_enabled"],
                    data_leaves_platform=payload["data_leaves_platform"],
                    is_approved=payload["is_approved"],
                    is_active=True,
                    metadata_json=payload["metadata"],
                    created_by_user_id=actor_user_id,
                )
                await self.models.create(model)
                if actor_user_id is not None:
                    await self.audit.log_model_registered(
                        actor_user_id,
                        model.id,
                        metadata={"code": model.code, "source": GPTLAB_METADATA_SOURCE},
                    )
                result.created += 1
            else:
                existing.name = payload["name"]
                existing.provider = payload["provider"]
                existing.model_type = payload["model_type"]
                existing.endpoint_url = payload["endpoint_url"]
                existing.data_retention_policy = payload["data_retention_policy"]
                existing.logging_enabled = payload["logging_enabled"]
                existing.data_leaves_platform = payload["data_leaves_platform"]
                existing.metadata_json = payload["metadata"]
                existing.is_active = True
                await self.models.update(existing)
                if actor_user_id is not None:
                    await self.audit.log_model_updated(
                        actor_user_id,
                        existing.id,
                        metadata={"code": existing.code, "source": GPTLAB_METADATA_SOURCE},
                    )
                result.updated += 1

            result.models_synced.append(ollama_id)

        if deactivate_missing:
            result.deactivated = await self._deactivate_stale(seen_codes, actor_user_id)

        if deactivate_demos:
            result.demos_deactivated = await self._deactivate_demos(actor_user_id)

        return result

    async def _deactivate_stale(
        self, seen_codes: set[str], actor_user_id: UUID | None
    ) -> int:
        stale = await self.models.list_by_code_prefix(GPTLAB_CODE_PREFIX)
        count = 0
        for model in stale:
            if model.code in seen_codes or not model.is_active:
                continue
            model.is_active = False
            await self.models.update(model)
            if actor_user_id is not None:
                await self.audit.log_model_updated(
                    actor_user_id,
                    model.id,
                    metadata={"code": model.code, "deactivated": True, "reason": "gptlab_sync"},
                )
            count += 1
        return count

    async def _deactivate_demos(self, actor_user_id: UUID | None) -> int:
        count = 0
        for code in DEMO_MODEL_CODES:
            model = await self.models.get_by_code(code)
            if model is None or not model.is_active:
                continue
            model.is_active = False
            await self.models.update(model)
            if actor_user_id is not None:
                await self.audit.log_model_updated(
                    actor_user_id,
                    model.id,
                    metadata={"code": model.code, "deactivated": True, "reason": "gptlab_sync"},
                )
            count += 1
        return count

    @staticmethod
    def _build_model_payload(
        *,
        code: str,
        ollama_id: str,
        api_base: str,
        farm: str,
        approve_new: bool,
    ) -> dict:
        return {
            "code": code,
            "name": display_name(ollama_id, farm),
            "provider": "GPT-Lab (TUNI)",
            "model_type": "open_source",
            "endpoint_url": api_base.rstrip("/"),
            "data_retention_policy": (
                "University GPU farm; prompts sent to TUNI GPT-Lab infrastructure"
            ),
            "logging_enabled": True,
            "data_leaves_platform": True,
            "is_approved": approve_new,
            "metadata": {
                "source": GPTLAB_METADATA_SOURCE,
                "farm": farm,
                "ollama_model_id": ollama_id,
                "api_style": "openai_compatible",
            },
        }
