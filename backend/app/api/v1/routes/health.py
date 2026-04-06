from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.request_context import get_request_id
from app.db.session import get_engine
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        request_id=get_request_id(),
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    settings = get_settings()
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return HealthResponse(
        status="ready",
        version=settings.app_version,
        environment=settings.environment,
        request_id=get_request_id(),
        timestamp=datetime.now(UTC),
    )
