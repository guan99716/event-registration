from datetime import datetime, timedelta, timezone
import jwt
import secrets
import hashlib
from app.config import settings


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload=payload, key=settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    decoded_payload = jwt.decode(
        jwt=token,
        key=settings.jwt_secret_key,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]},
    )
    return decoded_payload


def generate_refresh_token() -> str:
    # it return 43-character string
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    # it return 64-character hexadecimal string
    return hashlib.sha256(token.encode()).hexdigest()

