from datetime import UTC, datetime, timedelta
from secrets import compare_digest, token_urlsafe
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.refresh import RefreshSession
from app.models.user import User

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "HS256"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER = "x-csrf-token"
TOKEN_ACCESS = "access"
TOKEN_REFRESH = "refresh"


def create_access_token(email: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": email,
        "role": role,
        "typ": TOKEN_ACCESS,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, get_settings().JWT_SECRET, algorithm=JWT_ALGORITHM)


def issue_refresh_token(db: Session, user: User) -> str:
    now = datetime.now(UTC)
    jti = uuid4().hex
    expiry = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(
        RefreshSession(
            user_id=user.id,
            jti=jti,
            expires_at=expiry,
            revoked_at=None,
        )
    )
    db.commit()
    payload = {
        "sub": user.email,
        "role": user.role,
        "typ": TOKEN_REFRESH,
        "jti": jti,
        "iat": now,
        "exp": expiry,
    }
    return jwt.encode(payload, get_settings().JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, *, expected_typ: str | None = None) -> dict[str, str]:
    payload = jwt.decode(
        token,
        get_settings().JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
    typ = str(payload.get("typ", ""))
    if expected_typ is not None and typ != expected_typ:
        raise jwt.InvalidTokenError("typ")
    return {
        "email": str(payload["sub"]),
        "role": str(payload["role"]),
        "typ": typ,
        "jti": str(payload.get("jti", "")),
        "iat": str(payload.get("iat", "")),
    }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _session_by_jti(db: Session, jti: str) -> RefreshSession | None:
    if not jti:
        return None
    return db.scalar(select(RefreshSession).where(RefreshSession.jti == jti))


def decode_refresh_token(db: Session, token: str) -> dict[str, str]:
    payload = decode_token(token, expected_typ=TOKEN_REFRESH)
    session = _session_by_jti(db, payload["jti"])
    now = datetime.now(UTC)
    if (
        session is None
        or session.revoked_at is not None
        or _as_utc(session.expires_at) <= now
    ):
        raise jwt.InvalidTokenError("revoked")
    user = db.scalar(select(User).where(User.id == session.user_id))
    if user is None:
        raise jwt.InvalidTokenError("user")
    if user.auth_revoked_at is not None and payload["iat"]:
        issued = datetime.fromtimestamp(int(float(payload["iat"])), UTC)
        if issued <= _as_utc(user.auth_revoked_at):
            raise jwt.InvalidTokenError("revoked")
    return payload


def revoke_refresh_jti(db: Session, jti: str) -> None:
    session = _session_by_jti(db, jti)
    if session is None or session.revoked_at is not None:
        return
    session.revoked_at = datetime.now(UTC)
    db.commit()


def revoke_user_sessions(db: Session, user: User) -> None:
    now = datetime.now(UTC)
    user.auth_revoked_at = now
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.commit()


def new_csrf_token() -> str:
    return token_urlsafe(32)


def require_csrf(request: Request) -> None:
    header = request.headers.get(CSRF_HEADER, "").strip()
    cookie = request.cookies.get(CSRF_COOKIE_NAME, "").strip()
    if not header or not cookie or not compare_digest(header, cookie):
        raise HTTPException(
            status_code=403,
            detail="No se pudo completar la solicitud",
        )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    header = request.headers.get("authorization", "")
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        )
    try:
        payload = decode_token(parts[1], expected_typ=TOKEN_ACCESS)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        ) from None
    user = db.scalar(select(User).where(User.email == payload["email"]))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        )
    if user.auth_revoked_at is not None and payload["iat"]:
        issued = datetime.fromtimestamp(int(float(payload["iat"])), UTC)
        if issued <= _as_utc(user.auth_revoked_at):
            raise HTTPException(
                status_code=401,
                detail="No se pudo completar la solicitud",
            )
    request.state.user_id = user.id
    payload["role"] = user.role
    return payload


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "secure": True,
        "samesite": "none",
        "path": get_settings().REFRESH_COOKIE_PATH,
    }


def set_session_cookies(
    response: Response, refresh_token: str, csrf_token: str
) -> None:
    max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    flags = _cookie_kwargs()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        **flags,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        **flags,
    )


def clear_session_cookies(response: Response) -> None:
    flags = _cookie_kwargs()
    response.delete_cookie(key=REFRESH_COOKIE_NAME, **flags)
    response.delete_cookie(key=CSRF_COOKIE_NAME, **flags)
