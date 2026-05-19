"""Unit tests for monitoring event dispatcher and handler registry (no DB)."""

import pytest
from unittest.mock import MagicMock

from app.services.events.constants import PROMPT_SUBMITTED
from app.services.events.handlers.base import EventHandler
from app.services.events.handlers.registry import EventHandlerRegistry
from app.services.events.types import DomainEventEnvelope


class _RecordingHandler(EventHandler):
    def __init__(self):
        self.calls: list[dict] = []

    async def handle(self, db, payload):
        self.calls.append(payload)


@pytest.mark.asyncio
async def test_handler_registry_dispatches_by_type():
    registry = EventHandlerRegistry()
    handler = _RecordingHandler()
    registry.register(PROMPT_SUBMITTED, handler)

    db = MagicMock()
    await registry.dispatch(db, PROMPT_SUBMITTED, {"event_type": PROMPT_SUBMITTED})
    assert len(handler.calls) == 1


@pytest.mark.asyncio
async def test_handler_registry_global_handler():
    registry = EventHandlerRegistry()
    handler = _RecordingHandler()
    registry.register_global(handler)

    db = MagicMock()
    await registry.dispatch(db, "other.event", {"k": 1})
    assert len(handler.calls) == 1


def test_envelope_defaults():
    e = DomainEventEnvelope(event_type="test")
    assert e.severity == "info"
    assert e.source == "api"
    assert e.payload == {}
