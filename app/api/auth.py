from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth")
@auth_router.post("/register", status_code=201)
def register():
    pass