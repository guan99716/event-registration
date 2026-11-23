from fastapi.testclient import TestClient
import pytest
import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.services.auth import create_access_token, decode_access_token
from app.config import settings

client = TestClient(app)


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
    data = {"email": "valid-email@example.com", "password": "Test123456!"}
    response = client.post("/auth/register", json=data)
    assert response.status_code == 201
    # use this data to login, and it is expected to login successfully
    response = client.post("/auth/login", json=data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert (
        isinstance(response.json()["access_token"], str)
        and response.json()["access_token"] != ""
    )
    assert response.json()["token_type"] == "bearer"


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
