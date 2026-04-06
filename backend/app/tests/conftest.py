from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings, set_settings_override
from app.db.base import Base
from app.db.session import get_engine, get_session_factory, init_db
from app.main import create_app


@pytest.fixture()
def test_settings(tmp_path) -> Settings:
    database_path = tmp_path / "test.db"
    settings = Settings(
        environment="test",
        debug=False,
        database_url=f"sqlite:///{database_path}",
        jwt_secret_key="test-secret-that-is-long-enough-1234",
        cors_origins=["http://localhost:5173"],
        rate_limit_per_minute=1000,
        analysis_cache_hours=24,
    )
    set_settings_override(settings)
    init_db(settings.database_url)
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())
    return settings


@pytest.fixture()
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(test_settings: Settings) -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def registered_user(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "architect@example.com",
            "password": "StrongPass123!",
            "full_name": "Architect User",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return {
        "token": payload["access_token"],
        "user_id": payload["user"]["id"],
        "email": payload["user"]["email"],
    }


@pytest.fixture()
def auth_headers(registered_user: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {registered_user['token']}"}
