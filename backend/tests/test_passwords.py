import uuid

from app.core.db import get_session_factory
from app.core.passwords import verify_password
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import select


def test_register_stores_argon2id_hash_not_plaintext(client: TestClient) -> None:
    email = f"ana.hash.{uuid.uuid4().hex}@example.com"
    password = "secreto-valido"
    response = client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201

    session = get_session_factory()()
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    stored = user.password
    session.close()
    assert stored != password
    assert stored.startswith("$argon2id$")
    assert verify_password(password, stored)
    assert not verify_password("otra-clave", stored)
