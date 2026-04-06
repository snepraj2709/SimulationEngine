from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.db.session import get_session_factory, init_db
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.user_repository import UserRepository
from app.services.analysis_pipeline import AnalysisPipelineService
from app.services.auth_service import AuthService


async def seed_demo() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    session = get_session_factory()()
    try:
        user_repo = UserRepository(session)
        auth_service = AuthService(user_repo)
        user = user_repo.get_by_email(settings.demo_user_email)
        if user is None:
            user = auth_service.register_user(
                email=settings.demo_user_email,
                password=settings.demo_user_password,
                full_name="Decision Sim Demo",
            )
            session.commit()
        analysis_repo = AnalysisRepository(session)
        existing = analysis_repo.get_latest_by_user_and_url(user.id, "https://www.netflix.com")
        if existing and existing.status == "completed":
            print(f"Demo analysis already exists: {existing.id}")
            return
        analysis = analysis_repo.create(
            user_id=user.id,
            input_url="https://www.netflix.com/",
            normalized_url="https://www.netflix.com",
            status="queued",
        )
        session.commit()
        await AnalysisPipelineService(session).process_analysis(analysis.id)
        print("Seeded demo user and Netflix analysis.")
        print(f"email={settings.demo_user_email}")
        print(f"password={settings.demo_user_password}")
        print(f"analysis_id={analysis.id}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(seed_demo())
