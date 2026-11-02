from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, stored: str) -> bool:
    if not stored.startswith("$argon2"):
        return False
    try:
        return _hasher.verify(stored, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(stored: str) -> bool:
    if not stored.startswith("$argon2"):
        return True
    return _hasher.check_needs_rehash(stored)
