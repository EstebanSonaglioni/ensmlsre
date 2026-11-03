import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import (
    LimitBodySizeMiddleware,
    RequestContextMiddleware,
    RequestTimeoutMiddleware,
)
from app.routers import (
    auth,
    dashboard,
    health,
    notifications,
    products,
    questions,
    sells,
    stores,
    ws,
)

configure_logging()
settings = get_settings()
logger = structlog.get_logger("app")

app = FastAPI(title="MLSRE", docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(RequestTimeoutMiddleware)
app.add_middleware(LimitBodySizeMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(questions.router)
app.include_router(sells.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(ws.router)

HTTP_DETAIL_OVERRIDES = {
    "Not Found": "Recurso no encontrado",
    "Method Not Allowed": "Método no permitido",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if isinstance(exc.detail, str):
        detail = exc.detail
    else:
        detail = "No se pudo completar la solicitud"
    detail = HTTP_DETAIL_OVERRIDES.get(detail, detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Los datos enviados no son válidos"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, _exc: Exception
) -> JSONResponse:
    logger.exception("unhandled_error", method=request.method, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno"},
    )
