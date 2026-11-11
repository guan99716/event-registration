from fastapi import APIRouter
from app.schemas.user import UserCreate

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register", status_code=201)
def register(user_data: UserCreate):
    return {"message": "註冊成功"}
