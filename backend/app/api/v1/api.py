from fastapi import APIRouter

from app.api.v1.routes import analyses, auth, feedback, health

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
