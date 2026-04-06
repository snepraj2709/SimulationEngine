from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppException(401, "not_authenticated", "Authentication credentials were not provided.")
    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - library behavior
        raise AppException(401, "invalid_token", "Authentication token is invalid or expired.") from exc
    user_id = str(payload.get("sub", ""))
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise AppException(401, "invalid_token", "Authentication token is invalid or expired.")
    return user
