from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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
