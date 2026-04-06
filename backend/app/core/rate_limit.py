from collections import defaultdict, deque
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.request_context import get_request_id


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        now = time()
        bucket = self._buckets[client_ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Please retry later.",
                        "request_id": get_request_id(),
                    }
                },
            )
        bucket.append(now)
        return await call_next(request)
