from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email.lower()))

    def get_by_id(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def create(self, *, email: str, password_hash: str, full_name: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self.session.add(user)
        self.session.flush()
        return user
