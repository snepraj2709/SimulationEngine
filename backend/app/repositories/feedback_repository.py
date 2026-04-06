from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import FeedbackEvent


class FeedbackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_existing(self, *, user_id: str, simulation_run_id: str) -> FeedbackEvent | None:
        stmt = select(FeedbackEvent).where(
            FeedbackEvent.user_id == user_id,
            FeedbackEvent.simulation_run_id == simulation_run_id,
        )
        return self.session.scalar(stmt)

    def save(self, feedback: FeedbackEvent) -> FeedbackEvent:
        self.session.add(feedback)
        self.session.flush()
        return feedback
