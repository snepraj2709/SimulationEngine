from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserCreateRequest, UserLoginRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreateRequest, session: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(UserRepository(session))
    user = service.register_user(email=payload.email, password=payload.password, full_name=payload.full_name)
    session.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(UserRepository(session))
    user = service.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
