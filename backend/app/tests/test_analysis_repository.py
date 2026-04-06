from datetime import UTC, datetime

from app.models.analysis import Analysis
from app.models.user import User
from app.repositories.analysis_repository import AnalysisRepository


def test_repository_hides_legacy_and_demo_analyses(db_session) -> None:
    user = User(email="repo@example.com", password_hash="hash", full_name="Repo User")
    db_session.add(user)
    db_session.flush()

    repository = AnalysisRepository(db_session)
    active = repository.create(
        user_id=user.id,
        input_url="https://active.example/",
        normalized_url="https://active.example",
        status="completed",
        pipeline_version=Analysis.ACTIVE_PIPELINE_VERSION,
    )
    legacy = repository.create(
        user_id=user.id,
        input_url="https://legacy.example/",
        normalized_url="https://legacy.example",
        status="completed",
        pipeline_version=Analysis.LEGACY_PIPELINE_VERSION,
    )
    demo = repository.create(
        user_id=user.id,
        input_url="https://demo.example/",
        normalized_url="https://demo.example",
        status="completed",
        pipeline_version=Analysis.DEMO_PIPELINE_VERSION,
    )
    db_session.commit()

    listed = repository.list_for_user(user.id)

    assert [item.id for item in listed] == [active.id]
    assert repository.get_by_id_for_user(active.id, user.id) is not None
    assert repository.get_by_id_for_user(legacy.id, user.id) is None
    assert repository.get_by_id_for_user(demo.id, user.id) is None


def test_repository_cache_reuse_only_returns_active_pipeline(db_session) -> None:
    user = User(email="cache@example.com", password_hash="hash", full_name="Cache User")
    db_session.add(user)
    db_session.flush()

    repository = AnalysisRepository(db_session)
    repository.create(
        user_id=user.id,
        input_url="https://shared.example/",
        normalized_url="https://shared.example",
        status="completed",
        pipeline_version=Analysis.LEGACY_PIPELINE_VERSION,
    )
    active = repository.create(
        user_id=user.id,
        input_url="https://shared.example/",
        normalized_url="https://shared.example",
        status="completed",
        pipeline_version=Analysis.ACTIVE_PIPELINE_VERSION,
    )
    active.completed_at = datetime.now(UTC)
    db_session.commit()

    cached = repository.get_latest_completed_by_normalized_url("https://shared.example", cache_hours=24)

    assert cached is not None
    assert cached.id == active.id
