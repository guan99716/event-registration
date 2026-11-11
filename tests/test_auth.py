from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_success():

    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "Test123456!"}
    )

    assert response.status_code == 201

def test_register_invalid_email():
    response = client.post(
        "/auth/register",json={"email":"invalid-email", "password":"Test123456!"}
    )
    assert response.status_code == 422