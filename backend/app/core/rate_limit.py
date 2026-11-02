from collections import defaultdict, deque
from time import monotonic

_WINDOW_SECONDS = 60.0
_LOGIN_LIMIT = 5
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _hits.clear()


def allow_attempt(scope: str, key: str, *, limit: int = _LOGIN_LIMIT) -> bool:
    now = monotonic()
    bucket = _hits[(scope, key)]
    while bucket and now - bucket[0] > _WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def client_ip(host: str | None) -> str:
    return host or "unknown"
