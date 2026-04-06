from fastapi.testclient import TestClient


def test_register_login_and_me(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"


def test_protected_route_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/analyses")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
