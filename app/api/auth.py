from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.schemas.user import UserCreate
from app.database import engine
from app.models.user import User

auth_router = APIRouter(prefix="/auth")

password_hash = PasswordHash.recommended()


@auth_router.post("/register", status_code=201)
def register(user_data: UserCreate):
    with Session(engine) as db:
        stmt = select(User).where(User.email == user_data.email)
        result = db.execute(stmt)
        # email is unique, each email appears at most once
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already registered")
        else:
            hashed_password = password_hash.hash(user_data.password)
            new_user = User(email=user_data.email, hashed_password=hashed_password)
            db.add(new_user) # add to session
            db.commit() # write into db
            return {"message":"註冊完成"}
