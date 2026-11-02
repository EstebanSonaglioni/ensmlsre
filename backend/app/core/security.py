from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, Request, Response

from app.core.config import get_settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "HS256"
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"
CSRF_HEADER = "x-csrf-token"
TOKEN_ACCESS = "access"
TOKEN_REFRESH = "refresh"

_revoked_tokens: set[str] = set()
_revoked_after: dict[str, datetime] = {}


def create_token(
    email: str,
    role: str,
    *,
    token_type: str,
    minutes: int | None = None,
    days: int | None = None,
) -> str:
    now = datetime.now(UTC)
    if minutes is not None:
        expiry = now + timedelta(minutes=minutes)
    else:
        expiry = now + timedelta(days=days or REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "role": role,
        "typ": token_type,
        "iat": now,
        "exp": expiry,
    }
    return jwt.encode(payload, get_settings().JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(email: str, role: str) -> str:
    return create_token(
        email,
        role,
        token_type=TOKEN_ACCESS,
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_refresh_token(email: str, role: str) -> str:
    return create_token(
        email,
        role,
        token_type=TOKEN_REFRESH,
        days=REFRESH_TOKEN_EXPIRE_DAYS,
    )


def decode_token(token: str, *, expected_typ: str | None = None) -> dict[str, str]:
    if token in _revoked_tokens:
        raise jwt.InvalidTokenError("revoked")
    payload = jwt.decode(
        token,
        get_settings().JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    email = str(payload["sub"])
    typ = str(payload.get("typ", ""))
    if expected_typ is not None and typ != expected_typ:
        raise jwt.InvalidTokenError("typ")
    cutoff = _revoked_after.get(email)
    iat = payload.get("iat")
    if cutoff is not None and iat is not None:
        issued = datetime.fromtimestamp(int(iat), UTC)
        if issued <= cutoff:
            raise jwt.InvalidTokenError("revoked")
    return {"email": email, "role": str(payload["role"]), "typ": typ}


def revoke_token(token: str) -> None:
    _revoked_tokens.add(token)


def revoke_user(email: str) -> None:
    _revoked_after[email] = datetime.now(UTC)


def require_csrf(request: Request) -> None:
    if not request.headers.get(CSRF_HEADER, "").strip():
        raise HTTPException(
            status_code=403,
            detail="No se pudo completar la solicitud",
        )


def get_current_user(request: Request) -> dict[str, str]:
    header = request.headers.get("authorization", "")
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        )
    try:
        return decode_token(parts[1], expected_typ=TOKEN_ACCESS)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        ) from None


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="none",
    )
