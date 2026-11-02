import pytest
from app.core.config import Settings


def test_jwt_secret_rejects_placeholder() -> None:
    with pytest.raises(ValueError):
        Settings.jwt_secret_must_be_strong("change-me")


def test_jwt_secret_rejects_short_value() -> None:
    with pytest.raises(ValueError):
        Settings.jwt_secret_must_be_strong("corto")
