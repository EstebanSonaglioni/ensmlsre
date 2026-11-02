from decimal import Decimal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    email: str
    role: str
    access_token: str
    balance: Decimal = Decimal("0")
    display_name: str = ""
    has_avatar: bool = False


class ProfileResponse(BaseModel):
    email: str
    role: str
    display_name: str
    has_avatar: bool
    balance: Decimal = Decimal("0")
