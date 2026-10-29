import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from src.config import get_settings
from src.models.refresh_token import RefreshToken

settings = get_settings()
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


def _generate_raw_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token(user_id: int) -> tuple[str, RefreshToken]:
    """Создаёт refresh-токен и объект модели для сохранения в БД."""
    raw_token = _generate_raw_refresh_token()
    now = datetime.now(UTC)

    refresh_token_model = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        revoked=False,
        created_at=now,
    )

    return raw_token, refresh_token_model


def is_refresh_token_valid(refresh_token: RefreshToken) -> bool:
    if refresh_token.revoked:
        return False

    return refresh_token.expires_at > datetime.now(UTC)
