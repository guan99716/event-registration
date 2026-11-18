from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import settings

engine = create_engine(settings.database_url)
def get_db():
    with Session(engine) as db:
        yield db