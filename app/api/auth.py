from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.schemas.user import UserCreate, UserLogin
from app.models.user import User
from app.database import get_db
from app.services.auth import create_access_token

auth_router = APIRouter(prefix="/auth")

password_hash = PasswordHash.recommended()


@auth_router.post("/register", status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> dict[str,str]:
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
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> dict[str,str]:
    stmt = select(User).where(User.email == user_data.email)
    result = db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    else:
        valid = password_hash.verify(user_data.password, existing_user.hashed_password)
        if valid:
            access_token = create_access_token(existing_user.id)
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")
