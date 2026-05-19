import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.request_context import RequestContext, clear_request_context, set_request_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request metadata for audit logging for the duration of each HTTP request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        ctx = RequestContext(
            request_id=request_id,
            ip_address=_client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:2000] or None,
        )
        set_request_context(ctx)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    if request.client:
        return request.client.host[:45]
    return None
