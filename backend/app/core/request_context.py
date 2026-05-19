"""Per-request context for audit logging (IP, user agent, request id)."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequestContext:
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "request_context",
    default=None,
)


def set_request_context(ctx: RequestContext) -> None:
    _request_context.set(ctx)


def get_request_context() -> RequestContext | None:
    return _request_context.get()


def clear_request_context() -> None:
    _request_context.set(None)


def client_ip_from_headers(
    *,
    client_host: str | None,
    forwarded_for: str | None,
) -> str | None:
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()[:45]
    if client_host:
        return client_host[:45]
    return None
