from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import (
    REFRESH_COOKIE_NAME,
    TOKEN_REFRESH,
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_csrf,
    revoke_token,
    revoke_user,
    set_refresh_cookie,
)
from app.models.store import StoreMembership
from app.models.user import User
from app.schemas.auth import ProfileResponse, RegisterRequest, RegisterResponse

router = APIRouter(prefix="/auth")

_UNAUTHORIZED = "No se pudo completar la solicitud"
_INVALID = "Los datos enviados no son válidos"


def _avatars_dir() -> Path:
    path = Path(get_settings().PROFILE_IMAGES_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    return None


def _write_avatar(data: bytes) -> str:
    name = uuid4().hex
    dest = _avatars_dir() / name
    dest.write_bytes(data)
    return name


def _avatar_file(user: User) -> Path | None:
    if not user.avatar_path:
        return None
    stored = Path(user.avatar_path)
    if stored.is_file():
        return stored
    candidate = _avatars_dir() / stored.name
    if candidate.is_file():
        return candidate
    return None


def _profile(user: User) -> ProfileResponse:
    return ProfileResponse(
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        has_avatar=bool(user.avatar_path),
        balance=user.balance,
    )


def _sync_seller_role(db: Session, user: User) -> User:
    if user.role != "comprador":
        return user
    membership = db.scalar(
        select(StoreMembership.id).where(StoreMembership.user_id == user.id)
    )
    if membership is None:
        return user
    user.role = "vendedor"
    db.commit()
    db.refresh(user)
    return user


def _start_session(response: Response, user: User) -> RegisterResponse:
    access = create_access_token(user.email, user.role)
    refresh = create_refresh_token(user.email, user.role)
    set_refresh_cookie(response, refresh)
    return RegisterResponse(
        email=user.email,
        role=user.role,
        access_token=access,
        balance=user.balance,
        display_name=user.display_name,
        has_avatar=bool(user.avatar_path),
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="No se pudo completar el registro",
        )
    user = User(
        email=payload.email,
        password=payload.password,
        role="comprador",
        display_name="",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _start_session(response, user)


@router.post("/login", response_model=RegisterResponse)
def login(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or user.password != payload.password:
        raise HTTPException(
            status_code=401,
            detail="No se pudo iniciar sesión",
        )
    user = _sync_seller_role(db, user)
    return _start_session(response, user)


@router.get("/me", response_model=RegisterResponse)
def me(request: Request, db: Session = Depends(get_db)) -> RegisterResponse:
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    try:
        payload = decode_token(token, expected_typ=TOKEN_REFRESH)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED) from None
    user = db.scalar(select(User).where(User.email == payload["email"]))
    if user is None:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    user = _sync_seller_role(db, user)
    return RegisterResponse(
        email=user.email,
        role=user.role,
        access_token=create_access_token(user.email, user.role),
        balance=user.balance,
        display_name=user.display_name,
        has_avatar=bool(user.avatar_path),
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    display_name: str = Form(""),
    image: UploadFile | None = File(None),
) -> ProfileResponse:
    account = db.scalar(select(User).where(User.email == user["email"]))
    if account is None:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    name = display_name.strip()
    if len(name) > 80:
        raise HTTPException(status_code=422, detail=_INVALID)
    account.display_name = name
    if image is not None and image.filename:
        data = await image.read()
        if not data or _media_type(data) is None:
            raise HTTPException(status_code=422, detail=_INVALID)
        old = _avatar_file(account)
        account.avatar_path = _write_avatar(data)
        if old is not None and old.is_file():
            old.unlink(missing_ok=True)
    db.commit()
    db.refresh(account)
    return _profile(account)


@router.get("/profile/image")
def get_profile_image(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    account = db.scalar(select(User).where(User.email == user["email"]))
    if account is None:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    path = _avatar_file(account)
    if path is None:
        raise HTTPException(status_code=404, detail=_UNAUTHORIZED)
    data = path.read_bytes()
    media = _media_type(data) or "application/octet-stream"
    return Response(content=data, media_type=media)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    require_csrf(request)
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    try:
        payload = decode_token(token, expected_typ=TOKEN_REFRESH)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED) from None
    revoke_token(token)
    revoke_user(payload["email"])
    clear_refresh_cookie(response)
