from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_email(value)
        return value


class RegisterResponse(BaseModel):
    email: str
    role: str
    access_token: str
    csrf_token: str
    balance: Decimal = Decimal("0")
    display_name: str = ""
    has_avatar: bool = False


class ProfileResponse(BaseModel):
    email: str
    role: str
    display_name: str
    has_avatar: bool
    balance: Decimal = Decimal("0")
