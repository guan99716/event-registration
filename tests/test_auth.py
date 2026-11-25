from fastapi.testclient import TestClient
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.main import app
from app.services.auth import (
    create_access_token,
    decode_access_token,
    hash_refresh_token,
)
from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User

client = TestClient(app)
engine = create_engine(settings.database_url)


# register
def test_register_success():
    data = {"email": "test@example.com", "password": "Test123456!"}

    response = client.post("/auth/register", json=data)

    assert response.status_code == 201
    assert "password" not in response.json()


def test_register_invalid_email():
    data = {"email": "invalid-email", "password": "Test123456!"}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 422


def test_register_duplicate_email():
    data = {"email": "duplicate@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    response = client.post("/auth/register", json=data)
    assert response.status_code == 409


# login
def test_login_success():
    # register a valid account first
    user_data = {"email": "valid-email@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    # use this data to login, and it is expected to login successfully
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    # login data: "access_token", "refresh_token", "token_type"
    token_data = response.json()
    # access token
    assert "access_token" in token_data
    assert isinstance(token_data["access_token"], str)
    assert token_data["access_token"] != ""
    # refresh_token
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert isinstance(token_data["refresh_token"], str)
    assert token_data["refresh_token"] != ""
    # check refresh is stored in database
    with Session(engine) as db:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(token_data["refresh_token"])
        )
        stored_token = db.execute(stmt).scalar_one_or_none()
        # get user_id
        stmt = select(User).where(User.email == user_data["email"])
        user = db.execute(stmt).scalar_one_or_none()
        assert stored_token is not None
        assert stored_token.user_id == user.id


def test_login_wrong_password():
    data = {"email": "valid-email@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    wrong_data = {"email": "valid-email@example.com", "password": "wrong-password"}
    response = client.post("/auth/login", json=wrong_data)
    assert response.status_code == 401


def test_login_nonexistent_user():
    nonexistent_data = {
        "email": "nonexistent-email@example.com",
        "password": "password",
    }
    response = client.post("/auth/login", json=nonexistent_data)
    assert response.status_code == 401


# token
def test_decode_access_token():
    access_token = create_access_token(123)
    decoded_payload = decode_access_token(access_token)
    assert decoded_payload["sub"] == "123"


def test_decode_invalid_token():
    payload = {
        "sub": str(123),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    wrong_key = "this-is-a-different-test-secret-key-12345"
    invalid_token = jwt.encode(payload=payload, key=wrong_key, algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(invalid_token)


def test_decode_expired_token():
    payload = {
        "sub": str(123),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=15),
    }
    token = jwt.encode(payload=payload, key=settings.jwt_secret_key, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_refresh_token_success():
    # register
    user_data = {"email": "valid-email@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    # login
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    # get refresh token
    old_refresh_token = response.json()["refresh_token"]
    token_data = {"refresh_token": old_refresh_token}
    # get new tokens
    response = client.post("/auth/refresh", json=token_data)
    assert response.status_code == 200
    new_token_data = response.json()
    new_refresh_token = new_token_data["refresh_token"]
    new_access_token = new_token_data["access_token"]
    assert new_token_data["token_type"] == "bearer"
    assert isinstance(new_refresh_token, str)
    assert new_refresh_token != ""
    assert isinstance(new_access_token, str)
    assert new_access_token != ""
    # differ from the older one
    assert new_refresh_token != old_refresh_token

    # query by token_hash
    new_refresh_token_hashed = hash_refresh_token(new_refresh_token)
    old_refresh_token_hashed = hash_refresh_token(old_refresh_token)

    with Session(engine) as db:
        # check old refresh token is revoked in database
        stmt1 = select(RefreshToken).where(
            old_refresh_token_hashed == RefreshToken.token_hash
        )
        stored_token_old = db.execute(stmt1).scalar_one_or_none()
        assert stored_token_old is not None
        assert stored_token_old.revoked_at is not None

        # check new refresh token is in the database, and is not revoked
        stmt2 = select(RefreshToken).where(
            new_refresh_token_hashed == RefreshToken.token_hash
        )
        stored_token_new = db.execute(stmt2).scalar_one_or_none()
        assert stored_token_new is not None
        assert stored_token_new.revoked_at is None
        # check user_id is the same
        assert stored_token_new.user_id == stored_token_old.user_id


# me
def test_get_current_user_success():
    # register a user
    data = {"email": "test@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    # login and get access token
    response = client.post("/auth/login", json=data)
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    # check email is correct
    assert response.json()["email"] == data["email"]
    # response doesn't contain hashed password
    assert "hashed_password" not in response.json()


def test_get_current_user_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token():
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
