from fastapi.testclient import TestClient
from app.main import app

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
    client.post("/auth/register", json=data)
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
