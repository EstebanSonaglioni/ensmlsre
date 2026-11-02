import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings

logger = structlog.get_logger("app")

SKIP_ACCESS_LOG_PATHS = {"/health"}

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def _too_large() -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={"detail": "El cuerpo de la solicitud es demasiado grande"},
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled_error",
                method=request.method,
                path=request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Ocurrió un error interno"},
            )

        response.headers["X-Request-ID"] = request_id
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)

        if request.url.path not in SKIP_ACCESS_LOG_PATHS:
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                user_id=getattr(request.state, "user_id", None),
            )
        return response


class LimitBodySizeMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        max_bytes = get_settings().max_body_bytes
        headers = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        content_length = headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Encabezado Content-Length inválido"},
                )
                await response(scope, receive, send)
                return
            if length > max_bytes:
                await _too_large()(scope, receive, send)
                return

        total = 0

        async def limited_receive() -> dict:
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"") or b""
                total += len(body)
                if total > max_bytes:
                    raise _BodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await _too_large()(scope, receive, send)


class _BodyTooLarge(Exception):
    pass


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        settings = get_settings()
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=settings.request_timeout_seconds,
            )
        except TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "La solicitud excedió el tiempo máximo"},
            )
