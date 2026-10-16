"""
core/middleware.py

ASGI middleware for cross-cutting HTTP concerns.

Responsibilities:
- Assign a unique request ID (UUID) to every incoming request.
- Store the request ID in request.state and in the logging context variable
  so all log records within the request carry it automatically.
- Set X-Request-ID on every response so clients can correlate errors.
- Log basic request/response info (method, path, status, duration) at INFO
  level in development; WARNING+ in production for failed requests only.

Non-goals:
- Not responsible for authentication or authorization.
- Not responsible for audit logging (that is the application service's job).
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.logging import get_logger, request_id_var

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a request ID to every request and propagates it through:
    - request.state.request_id     (accessible to route handlers / error handlers)
    - core.logging.request_id_var  (automatically included in all log records)
    - X-Request-ID response header (returned to the client)
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Set context var so all log records in this request include the ID
        token = request_id_var.set(request_id)

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response



