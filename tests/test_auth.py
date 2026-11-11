from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_success():

    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "Test123456!"}
    )

    assert response.status_code == 201
