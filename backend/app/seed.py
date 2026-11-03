"""Carga usuarios y datos demo. Idempotente: si boss@mail.com existe, no hace nada."""

from __future__ import annotations

import os
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.bootstrap import prepare_schema
from app.core.db import get_session_factory
from app.core.passwords import hash_password
from app.models.message import SellMessage
from app.models.notification import Notification
from app.models.product import Product, ProductAnswer, ProductQuestion
from app.models.sell import Sell
from app.models.store import Store, StoreMembership
from app.models.user import User

logger = structlog.get_logger("app")

DEMO_BOSS = "boss@mail.com"
DEMO_SELLERS = ("ventas1@mail.com", "ventas2@mail.com")
DEMO_BUYERS = ("compras1@mail.com", "compras2@mail.com")
DEMO_STORE = "Almacén MLSRE"
_ZERO = Decimal("0.00")
_RNG = 42

_CATALOG: dict[str, tuple[str, str, str, str]] = {
    "aceite": ("3490.00", "620.00", "Alimentos", "Aceites"),
    "agua": ("890.00", "150.00", "Bebidas", "Sin alcohol"),
    "arroz": ("1890.00", "320.00", "Alimentos", "Almacén"),
    "cereal": ("2790.00", "480.00", "Alimentos", "Desayuno"),
    "chocolate": ("2190.00", "410.00", "Alimentos", "Golosinas"),
    "coca": ("1790.00", "300.00", "Bebidas", "Gaseosas"),
    "detergente": ("2490.00", "440.00", "Limpieza", "Ropa"),
    "fideos": ("1590.00", "280.00", "Alimentos", "Pastas"),
    "galletita": ("1390.00", "250.00", "Alimentos", "Galletitas"),
    "jabon": ("990.00", "180.00", "Limpieza", "Higiene"),
    "jugo": ("1290.00", "220.00", "Bebidas", "Jugos"),
    "leche": ("1690.00", "290.00", "Alimentos", "Lácteos"),
    "mermelada": ("2390.00", "400.00", "Alimentos", "Dulces"),
    "pasta": ("2190.00", "380.00", "Alimentos", "Pastas"),
    "tomate": ("1490.00", "260.00", "Alimentos", "Conservas"),
}

_QUESTIONS = (
    "Todavía está fresco?",
    "Hacen envío al centro?",
    "Hay más unidades?",
    "La fecha de vencimiento es cercana?",
    "Se puede retirar hoy?",
    "Urgente: confirman stock?",
    "El precio incluye IVA?",
    "Aceptan transferencia?",
    "Viene en pack o suelto?",
    "Es el mismo de la foto?",
)


def _money(value: str | Decimal | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _demo_password() -> str:
    return os.environ.get("DEMO_PASSWORD", "mlsre-demo")


def _images_dir() -> Path:
    env = os.environ.get("SEED_IMAGES_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "seed" / "products"


def _product_images_dir() -> Path:
    from app.core.config import get_settings

    path = Path(get_settings().PRODUCT_IMAGES_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _seed_files() -> list[Path]:
    image_root = _images_dir()
    files = sorted(
        p
        for p in image_root.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not files:
        raise RuntimeError(f"no hay imágenes de seed en {image_root}")
    return files


def _copy_image(src: Path) -> str:
    dest = _product_images_dir() / src.name
    dest.write_bytes(src.read_bytes())
    return src.name


def _attach_images(db: Session, files: list[Path]) -> int:
    by_stem = {path.stem: path for path in files}
    products = db.scalars(
        select(Product)
        .join(Store, Store.id == Product.store_id)
        .where(Store.name == DEMO_STORE, Product.name.in_(tuple(by_stem)))
    ).all()
    updated = 0
    for product in products:
        src = by_stem.get(product.name)
        if src is None:
            continue
        product.image_path = _copy_image(src)
        updated += 1
    return updated


def _user(
    db: Session,
    email: str,
    role: str,
    display_name: str,
    hashed: str,
) -> User:
    user = User(
        email=email,
        password=hashed,
        role=role,
        display_name=display_name,
        balance=_ZERO,
    )
    db.add(user)
    db.flush()
    return user


def _notify(
    db: Session,
    *,
    user_id: int,
    kind: str,
    title: str,
    body: str,
    when: datetime,
    sell_id: int | None = None,
    product_id: int | None = None,
) -> None:
    db.add(
        Notification(
            user_id=user_id,
            sell_id=sell_id,
            product_id=product_id,
            kind=kind,
            title=title,
            body=body,
            created_at=when,
        )
    )


def seed_demo(db: Session) -> bool:
    files = _seed_files()
    if db.scalar(select(User.id).where(User.email == DEMO_BOSS)) is not None:
        linked = _attach_images(db, files)
        db.commit()
        logger.info("seed_skipped", reason="already_present", images=linked)
        return False

    hashed = hash_password(_demo_password())
    boss = _user(db, DEMO_BOSS, "vendedor", "Boss", hashed)
    ventas1 = _user(db, DEMO_SELLERS[0], "vendedor", "Ventas 1", hashed)
    ventas2 = _user(db, DEMO_SELLERS[1], "vendedor", "Ventas 2", hashed)
    compras1 = _user(db, DEMO_BUYERS[0], "comprador", "Compras 1", hashed)
    compras2 = _user(db, DEMO_BUYERS[1], "comprador", "Compras 2", hashed)
    buyers = (compras1, compras2)
    sellers = (ventas1, ventas2)

    store = Store(name=DEMO_STORE)
    db.add(store)
    db.flush()
    db.add(StoreMembership(store_id=store.id, user_id=boss.id, role="admin"))
    db.add(StoreMembership(store_id=store.id, user_id=ventas1.id, role="vendedor"))
    db.add(StoreMembership(store_id=store.id, user_id=ventas2.id, role="vendedor"))

    products: list[Product] = []
    for index, path in enumerate(files):
        stem = path.stem
        price, profit, category, subcategory = _CATALOG.get(
            stem.lower(),
            ("1590.00", "250.00", "Alimentos", "Almacén"),
        )
        seller = sellers[index % 2]
        product = Product(
            store_id=store.id,
            seller_user_id=seller.id,
            name=stem,
            quantity=400,
            price=_money(price),
            net_profit=_money(profit),
            category=category,
            subcategory=subcategory,
            image_path=_copy_image(path),
            paused=False,
            ships=True,
            pickup=True,
        )
        db.add(product)
        db.flush()
        products.append(product)

    rng = random.Random(_RNG)
    now = datetime.now(UTC)
    start = now - timedelta(days=89)
    payments = ("tarjeta", "transferencia", "efectivo")
    fulfillments = ("envio", "retiro")
    completed: list[Sell] = []

    for day in range(90):
        moment = start + timedelta(
            days=day, hours=rng.randint(9, 20), minutes=rng.randint(0, 59)
        )
        if day % 11 == 3:
            continue
        extra = 2 if day % 6 == 0 else 0
        for _ in range(1 + (day % 3) + extra):
            product = rng.choice(products)
            buyer = rng.choice(buyers)
            qty = rng.choice((1, 1, 1, 2, 3))
            if product.quantity < qty:
                continue
            fulfillment = rng.choice(fulfillments)
            payment = rng.choice(payments)
            subtotal = _money(product.price * qty)
            sell = Sell(
                buyer_user_id=buyer.id,
                seller_user_id=product.seller_user_id,
                product_id=product.id,
                store_id=store.id,
                quantity=qty,
                unit_price=product.price,
                subtotal=subtotal,
                fulfillment=fulfillment,
                payment_method=payment,
                status="completada",
                checkout_id=uuid4().hex,
                eta_at=moment + timedelta(days=2) if fulfillment == "envio" else None,
                created_at=moment - timedelta(hours=6),
                updated_at=moment,
            )
            product.quantity -= qty
            owner = (
                ventas1 if product.seller_user_id == ventas1.id else ventas2
            )
            owner.balance = _money((owner.balance or _ZERO) + subtotal)
            db.add(sell)
            db.flush()
            completed.append(sell)
            _notify(
                db,
                user_id=product.seller_user_id,
                kind="venta",
                title="Nueva venta",
                body=f"Compraron {product.name}",
                when=sell.created_at,
                sell_id=sell.id,
                product_id=product.id,
            )

    open_specs = (
        ("en_curso", 4),
        ("en_viaje", 3),
        ("esperando_retiro", 3),
        ("en_carrito", 3),
        ("cancelada", 8),
        ("reembolsada", 5),
    )
    for status, count in open_specs:
        for _ in range(count):
            product = rng.choice(products)
            buyer = rng.choice(buyers)
            qty = 1
            when = now - timedelta(days=rng.randint(0, 20), hours=rng.randint(1, 12))
            paid = status not in {"en_carrito", "cancelada"}
            if paid and product.quantity >= qty:
                product.quantity -= qty
                if status != "reembolsada":
                    owner = (
                        ventas1
                        if product.seller_user_id == ventas1.id
                        else ventas2
                    )
                    owner.balance = _money(
                        (owner.balance or _ZERO) + product.price
                    )
            if status == "esperando_retiro":
                fulfillment = "retiro"
            else:
                fulfillment = rng.choice(fulfillments)
            sell = Sell(
                buyer_user_id=buyer.id,
                seller_user_id=product.seller_user_id,
                product_id=product.id,
                store_id=store.id,
                quantity=qty,
                unit_price=product.price,
                subtotal=product.price,
                fulfillment=fulfillment,
                payment_method=None if status == "en_carrito" else rng.choice(payments),
                status=status,
                checkout_id=None if status == "en_carrito" else uuid4().hex,
                eta_at=when + timedelta(days=1) if fulfillment == "envio" else None,
                created_at=when,
                updated_at=when + timedelta(hours=3),
            )
            db.add(sell)
            db.flush()
            if status == "cancelada":
                _notify(
                    db,
                    user_id=product.seller_user_id,
                    kind="estado",
                    title="Venta cancelada",
                    body=f"Cancelaron {product.name}",
                    when=sell.updated_at,
                    sell_id=sell.id,
                    product_id=product.id,
                )

    for sell in completed[::7]:
        asked = sell.created_at + timedelta(minutes=20)
        db.add(
            SellMessage(
                sell_id=sell.id,
                sender_user_id=sell.buyer_user_id,
                body="Hola, confirman el horario?",
                created_at=asked,
            )
        )
        db.add(
            SellMessage(
                sell_id=sell.id,
                sender_user_id=sell.seller_user_id,
                body="Sí, queda para hoy.",
                created_at=asked + timedelta(hours=1),
            )
        )
        _notify(
            db,
            user_id=sell.seller_user_id,
            kind="mensaje",
            title="Mensaje en la orden",
            body="Hola, confirman el horario?",
            when=asked,
            sell_id=sell.id,
        )

    for index, product in enumerate(products):
        buyer = buyers[index % 2]
        asked_at = now - timedelta(days=rng.randint(1, 80), hours=rng.randint(1, 10))
        question = ProductQuestion(
            product_id=product.id,
            asker_user_id=buyer.id,
            text=_QUESTIONS[index % len(_QUESTIONS)],
            created_at=asked_at,
        )
        db.add(question)
        db.flush()
        _notify(
            db,
            user_id=product.seller_user_id,
            kind="pregunta",
            title="Nueva pregunta",
            body=question.text,
            when=asked_at,
            product_id=product.id,
        )
        if index % 3 != 0:
            answered_at = asked_at + timedelta(hours=rng.randint(2, 48))
            db.add(
                ProductAnswer(
                    question_id=question.id,
                    responder_user_id=product.seller_user_id,
                    text="Sí, hay stock y se puede retirar o enviar.",
                    created_at=answered_at,
                )
            )
            _notify(
                db,
                user_id=buyer.id,
                kind="respuesta",
                title="Respondieron tu pregunta",
                body="Sí, hay stock y se puede retirar o enviar.",
                when=answered_at,
                product_id=product.id,
            )

    extra_unanswered = ProductQuestion(
        product_id=products[0].id,
        asker_user_id=compras2.id,
        text="Urgente: lo necesitan para hoy a la tarde?",
        created_at=now - timedelta(hours=6),
    )
    db.add(extra_unanswered)
    db.flush()
    _notify(
        db,
        user_id=products[0].seller_user_id,
        kind="pregunta",
        title="Nueva pregunta",
        body=extra_unanswered.text,
        when=extra_unanswered.created_at,
        product_id=products[0].id,
    )

    db.commit()
    logger.info(
        "seed_done",
        products=len(products),
        sells=db.scalar(select(func.count(Sell.id))) or 0,
    )
    return True


def main() -> None:
    prepare_schema()
    session = get_session_factory()()
    try:
        seed_demo(session)
    except Exception:
        session.rollback()
        logger.exception("seed_failed")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
