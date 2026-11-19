import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine

@pytest.fixture(autouse=True)
def clean_test_db():
    assert engine.url.database == "event_test_db"

    with Session(engine) as db:
        db.execute(text(
            "TRUNCATE TABLE users, events, registrations, "
            "refresh_tokens RESTART IDENTITY CASCADE"
        ))
        db.commit()