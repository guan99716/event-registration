from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timezone, timedelta

from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import RefreshTokenRequest
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.database import get_db
from app.services.auth import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)

auth_router = APIRouter(prefix="/auth")
bearer_auth = HTTPBearer()

password_hash = PasswordHash.recommended()


@auth_router.post("/register", status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    stmt = select(User).where(User.email == user_data.email)
    result = db.execute(stmt)
    # email is unique, each email appears at most once
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    else:
        hashed_password = password_hash.hash(user_data.password)
        new_user = User(email=user_data.email, hashed_password=hashed_password)
        db.add(new_user)  # add to session
        db.commit()  # write into db
        return {"message": "Registration complete"}


@auth_router.post("/login", status_code=200)
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> dict[str, str]:
    stmt = select(User).where(User.email == user_data.email)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    else:
        # if password valid, return access token, else raise error
        valid = password_hash.verify(user_data.password, user.hashed_password)
        if valid:
            access_token = create_access_token(user.id)
            refresh_token = generate_refresh_token()
            refresh_token_hashed = hash_refresh_token(refresh_token)
            # store refresh_token_hashed to database
            new_refresh_token_hashed = RefreshToken(
                user_id=user.id,
                token_hash=refresh_token_hashed,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            db.add(new_refresh_token_hashed)
            db.commit()
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")


# use Depencds(bearer_auth) to get bearer token
@auth_router.get("/me", status_code=200)
def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_auth),
    db: Session = Depends(get_db),
):
    # payload should contains sub and exp
    try:
        payload = decode_access_token(auth.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    sub = payload["sub"]

    # user_id should be integer
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user id")

    # query the user table to find user data, where User.id == user_id
    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return {"id": user.id, "email": user.email, "role": user.role}
    else:
        raise HTTPException(status_code=401, detail="Invalid user id")


@auth_router.post("/refresh", status_code=200)
def request_refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    refresh_token_hashed = hash_refresh_token(data.refresh_token)
    stmt = select(RefreshToken).where(refresh_token_hashed == RefreshToken.token_hash)
    result = db.execute(stmt)
    stored_token = result.scalar_one_or_none()
    if not stored_token:
        raise HTTPException(status_code=401, detail="Invalid fresh token")
    else:
        if (
            stored_token.expires_at <= datetime.now(timezone.utc)
            or stored_token.revoked_at is not None
        ):
            raise HTTPException(status_code=401, detail="Invalid fresh token")
        else:
            # generate new access and refresh tokens
            access_token = create_access_token(stored_token.user_id)
            refresh_token = generate_refresh_token()
            refresh_token_hashed = hash_refresh_token(refresh_token)
            stored_token.revoked_at = datetime.now(timezone.utc)
            new_token = RefreshToken(
                user_id=stored_token.user_id,
                token_hash=refresh_token_hashed,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            db.add(new_token)
            db.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
