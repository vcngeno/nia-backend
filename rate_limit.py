"""Small in-process rate limiter for sensitive API endpoints.

This protects a single application instance. Multi-instance deployments should
replace the store with Redis or a platform-provided distributed limiter.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds

        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= cutoff:
                requests.popleft()

            if len(requests) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(window_seconds)},
                )

            requests.append(now)


limiter = InMemoryRateLimiter()


def _client_key(request: Request, endpoint: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{endpoint}:{client_host}"


def rate_limit_pin_login(request: Request) -> None:
    limiter.check(_client_key(request, "pin-login"), limit=5, window_seconds=60)


def rate_limit_chat(request: Request) -> None:
    limiter.check(_client_key(request, "chat"), limit=30, window_seconds=60)
