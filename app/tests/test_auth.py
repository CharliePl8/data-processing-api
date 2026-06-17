from fastapi.testclient import TestClient

from app.main import app
from app.core.config import API_AUTH_USERNAME, API_AUTH_PASSWORD


client = TestClient(app)


def test_token_endpoint_success():
    response = client.post(
        "/token",
        data={"username": API_AUTH_USERNAME, "password": API_AUTH_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_token_endpoint_failure():
    response = client.post(
        "/token",
        data={"username": "wrong", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_token():
    response = client.post("/upload", files={"file": ("test.csv", "a,b\n1,2\n")})
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    auth_response = client.post(
        "/token",
        data={"username": API_AUTH_USERNAME, "password": API_AUTH_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = auth_response.json()["access_token"]
    response = client.post(
        "/upload",
        files={"file": ("test.csv", "a,b\n1,2\n")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
