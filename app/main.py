from fastapi import FastAPI
from app.api.auth import auth_router
app = FastAPI()

app.include_router(auth_router)
@app.get('/health')
def check_health():
    return {'status': 'ok'}