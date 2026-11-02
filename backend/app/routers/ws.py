import asyncio
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.core.security import TOKEN_ACCESS, decode_token
from app.core.ws_hub import hub
from app.models.product import Product
from app.models.sell import Sell
from app.models.store import StoreMembership
from app.models.user import User

router = APIRouter()


def _can_view(db, sell: Sell, user: User) -> bool:
    if sell.buyer_user_id == user.id or sell.seller_user_id == user.id:
        return True
    membership = db.scalar(
        select(StoreMembership).where(
            StoreMembership.store_id == sell.store_id,
            StoreMembership.user_id == user.id,
            StoreMembership.role == "admin",
        )
    )
    return membership is not None


def _can_view_product(db, product: Product, user: User) -> bool:
    if not product.paused:
        return True
    if product.seller_user_id == user.id:
        return True
    membership = db.scalar(
        select(StoreMembership).where(
            StoreMembership.store_id == product.store_id,
            StoreMembership.user_id == user.id,
            StoreMembership.role == "admin",
        )
    )
    return membership is not None


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    origin = ws.headers.get("origin", "")
    if origin and origin not in get_settings().cors_origin_list:
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_json(), timeout=10)
    except (TimeoutError, WebSocketDisconnect, ValueError):
        await ws.close(code=1008)
        return
    if not isinstance(first, dict) or first.get("type") != "auth":
        await ws.close(code=1008)
        return
    token = first.get("token")
    if not isinstance(token, str) or not token:
        await ws.close(code=1008)
        return
    try:
        payload = decode_token(token, expected_typ=TOKEN_ACCESS)
    except jwt.InvalidTokenError:
        await ws.close(code=1008)
        return
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.email == payload["email"]))
        if user is None:
            await ws.close(code=1008)
            return
        if user.auth_revoked_at is not None and payload["iat"]:
            issued = datetime.fromtimestamp(int(float(payload["iat"])), UTC)
            if issued <= user.auth_revoked_at:
                await ws.close(code=1008)
                return
        user_id = user.id
        hub.connect(user_id, ws)
        try:
            while True:
                message = await ws.receive_json()
                if not isinstance(message, dict):
                    continue
                kind = message.get("type")
                if kind not in {"watch", "unwatch"}:
                    continue
                sell_id = message.get("sell_id")
                product_id = message.get("product_id")
                if isinstance(sell_id, int):
                    sell = session.scalar(select(Sell).where(Sell.id == sell_id))
                    if sell is None or sell.status == "en_carrito":
                        continue
                    if not _can_view(session, sell, user):
                        continue
                    if kind == "watch":
                        hub.watch(user_id, sell_id, ws)
                    else:
                        hub.unwatch(user_id, sell_id, ws)
                elif isinstance(product_id, int):
                    product = session.scalar(
                        select(Product).where(Product.id == product_id)
                    )
                    if product is None or not _can_view_product(session, product, user):
                        continue
                    if kind == "watch":
                        hub.watch_product(user_id, product_id, ws)
                    else:
                        hub.unwatch_product(user_id, product_id, ws)
        except WebSocketDisconnect:
            pass
        finally:
            hub.disconnect(user_id, ws)
    finally:
        session.close()
