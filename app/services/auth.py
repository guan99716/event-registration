from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload=payload, key=settings.jwt_secret_key, algorithm="HS256")
