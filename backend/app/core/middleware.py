import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings

logger = structlog.get_logger("app")

SKIP_ACCESS_LOG_PATHS = {"/health"}


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
        response.headers["X-Content-Type-Options"] = "nosniff"

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


class LimitBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Encabezado Content-Length inválido"},
                )
            if length > settings.max_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "El cuerpo de la solicitud es demasiado grande"},
                )
        return await call_next(request)


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
