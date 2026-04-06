from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, *, email: str, password: str, full_name: str) -> User:
        if self.user_repository.get_by_email(email):
            raise AppException(409, "email_exists", "An account already exists for this email address.")
        return self.user_repository.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
        )

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppException(401, "invalid_credentials", "Incorrect email or password.")
        return user
