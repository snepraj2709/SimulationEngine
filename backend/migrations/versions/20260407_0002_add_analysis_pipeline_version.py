"""Add analysis pipeline version

Revision ID: 20260407_0002
Revises: 20260406_0001
Create Date: 2026-04-07 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260407_0002"
down_revision: str | None = "20260406_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analyses",
        sa.Column("pipeline_version", sa.String(length=64), nullable=False, server_default="llm-v1"),
    )
    op.execute("UPDATE analyses SET pipeline_version = 'legacy-deterministic-v1'")
    op.execute(
        """
        UPDATE analyses
        SET pipeline_version = 'demo-netflix-v1'
        WHERE user_id IN (
            SELECT id FROM users WHERE email = 'demo@example.com'
        )
        """
    )
    op.alter_column("analyses", "pipeline_version", server_default="llm-v1")


def downgrade() -> None:
    op.drop_column("analyses", "pipeline_version")
