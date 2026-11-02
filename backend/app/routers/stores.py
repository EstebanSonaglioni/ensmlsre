from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.store import Store, StoreInvitation, StoreMembership
from app.models.user import User
from app.schemas.stores import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    CreateInvitationRequest,
    CreateInvitationResponse,
    CreateStoreRequest,
    CreateStoreResponse,
    InvitationItem,
    InvitationListResponse,
    StoreItem,
    StoreListResponse,
)

router = APIRouter(prefix="/stores")


def _user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="No se pudo completar la solicitud",
        )
    return user


@router.post("", response_model=CreateStoreResponse, status_code=201)
def create_store(
    payload: CreateStoreRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateStoreResponse:
    owner = _user_by_email(db, user["email"])
    store = Store(name=payload.name)
    db.add(store)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear la tienda",
        ) from None
    db.add(StoreMembership(store_id=store.id, user_id=owner.id, role="admin"))
    if owner.role == "comprador":
        owner.role = "vendedor"
    db.commit()
    return CreateStoreResponse(id=store.id, name=payload.name, role="admin")


@router.get("", response_model=StoreListResponse)
def list_stores(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> StoreListResponse:
    query = (
        select(Store.id, Store.name, StoreMembership.role)
        .join(Store, Store.id == StoreMembership.store_id)
        .join(User, User.id == StoreMembership.user_id)
        .where(User.email == user["email"])
    )
    needle = q.strip().casefold()
    if needle:
        query = query.where(func.lower(Store.name).contains(needle))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    rows = db.execute(query.offset(start).limit(page_size)).all()
    return StoreListResponse(
        items=[
            StoreItem(id=store_id, name=name, role=role)
            for store_id, name, role in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/invitations", response_model=InvitationListResponse)
def list_invitations(
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> InvitationListResponse:
    query = (
        select(StoreInvitation.email, Store.name)
        .join(Store, Store.id == StoreInvitation.store_id)
        .where(StoreInvitation.email == user["email"])
    )
    needle = q.strip().casefold()
    if needle:
        query = query.where(
            func.lower(Store.name).contains(needle)
            | func.lower(StoreInvitation.email).contains(needle)
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    start = (page - 1) * page_size
    rows = db.execute(query.offset(start).limit(page_size)).all()
    return InvitationListResponse(
        items=[InvitationItem(email=email, store=store) for email, store in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/invitations", response_model=CreateInvitationResponse, status_code=201)
def create_invitation(
    payload: CreateInvitationRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateInvitationResponse:
    is_admin = db.scalar(
        select(StoreMembership.id)
        .join(Store, Store.id == StoreMembership.store_id)
        .join(User, User.id == StoreMembership.user_id)
        .where(
            User.email == user["email"],
            Store.name == payload.store,
            StoreMembership.role == "admin",
        )
    )
    if is_admin is None:
        raise HTTPException(
            status_code=403,
            detail="No se pudo crear la invitación",
        )
    store = db.scalar(select(Store).where(Store.name == payload.store))
    if store is None:
        raise HTTPException(
            status_code=403,
            detail="No se pudo crear la invitación",
        )
    db.add(StoreInvitation(store_id=store.id, email=payload.email))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear la invitación",
        ) from None
    return CreateInvitationResponse(email=payload.email, store=payload.store)


@router.post("/invitations/accept", response_model=AcceptInvitationResponse)
def accept_invitation(
    payload: AcceptInvitationRequest,
    user: dict[str, str] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AcceptInvitationResponse:
    invitation = db.scalar(
        select(StoreInvitation)
        .join(Store, Store.id == StoreInvitation.store_id)
        .where(
            StoreInvitation.email == user["email"],
            Store.name == payload.store,
        )
    )
    if invitation is None:
        raise HTTPException(
            status_code=404,
            detail="No se pudo aceptar la invitación",
        )
    invitee = _user_by_email(db, user["email"])
    db.add(
        StoreMembership(
            store_id=invitation.store_id,
            user_id=invitee.id,
            role="vendedor",
        )
    )
    db.delete(invitation)
    if invitee.role == "comprador":
        invitee.role = "vendedor"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo aceptar la invitación",
        ) from None
    return AcceptInvitationResponse(store=payload.store, role="vendedor")
