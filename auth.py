"""Password hashing and verification. Plaintext passwords are never stored here."""

from pwdlib import PasswordHash


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("A password is required.")
    return _password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    if not password or not stored_hash:
        return False
    try:
        return _password_hash.verify(password, stored_hash)
    except (TypeError, ValueError):
        return False
