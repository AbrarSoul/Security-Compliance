"""Shared helpers for Sprint 3 integration and E2E tests."""

from __future__ import annotations

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.services.events.outbox_processor import OutboxProcessor

from tests.helpers.integration import (
    auth_headers,
    get_seed_model,
    run_scan,
    skip_if_no_db,
    upload_dataset,
)


async def process_outbox(*, max_rounds: int = 10) -> int:
    """Drain pending outbox rows (worker disabled in pytest). Returns total processed."""
    processor = OutboxProcessor(AsyncSessionLocal, batch_size=50)
    total = 0
    for _ in range(max_rounds):
        n = await processor.process_batch()
        total += n
        if n == 0:
            break
    return total


async def open_monitoring_session(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    execution_request_id: str | None = None,
) -> dict:
    body: dict = {}
    if execution_request_id:
        body["execution_request_id"] = execution_request_id
    resp = await client.post("/api/v1/monitoring/sessions", json=body, headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def setup_execution_for_monitoring(
    client: AsyncClient,
    headers: dict[str, str],
) -> tuple[dict, dict, str]:
    """Upload clean dataset, scan, validate execution. Returns (file, scan, execution_id)."""
    file_rec = await upload_dataset(client, headers, "minimal_clean.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")
    validate = await client.post(
        "/api/v1/executions/validate",
        headers=headers,
        json={
            "dataset_id": file_rec["id"],
            "scan_id": scan["id"],
            "model_id": model["id"],
            "execution_purpose": "Sprint 3 integration test",
        },
    )
    skip_if_no_db(validate)
    assert validate.status_code == 201, validate.text
    body = validate.json()
    if body["decision"] == "block":
        raise AssertionError(f"Expected allow/warn execution, got block: {body}")
    return file_rec, scan, body["execution_request_id"]


async def guard_prompt(
    client: AsyncClient,
    headers: dict[str, str],
    execution_id: str,
    prompt: str,
    *,
    session_id: str | None = None,
) -> dict:
    payload: dict = {"prompt": prompt}
    if session_id:
        payload["session_id"] = session_id
    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/prompt",
        headers=headers,
        json=payload,
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def guard_output(
    client: AsyncClient,
    headers: dict[str, str],
    execution_id: str,
    output: str,
    *,
    session_id: str | None = None,
) -> dict:
    payload: dict = {"output": output}
    if session_id:
        payload["session_id"] = session_id
    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/output",
        headers=headers,
        json=payload,
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200, resp.text
    return resp.json()
