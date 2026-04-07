"""Add staged workflow support

Revision ID: 20260407_0003
Revises: 20260407_0002
Create Date: 2026-04-07 00:30:00
"""

from collections.abc import Sequence
import json

from alembic import op
import sqlalchemy as sa


revision: str = "20260407_0003"
down_revision: str | None = "20260407_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    default_state = json.dumps(
        {
            "product_understanding": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            },
            "icp_profiles": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            },
            "scenarios": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            },
            "decision_flow": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            },
            "final_review": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            },
        }
    )
    final_state = json.dumps(
        {
            stage: {
                "status": "completed",
                "started_at": None,
                "completed_at": None,
                "edited": False,
                "error_message": None,
            }
            for stage in (
                "product_understanding",
                "icp_profiles",
                "scenarios",
                "decision_flow",
                "final_review",
            )
        }
    )

    op.add_column(
        "analyses",
        sa.Column("current_stage", sa.String(length=64), nullable=False, server_default="product_understanding"),
    )
    op.add_column(
        "analyses",
        sa.Column("workflow_state_json", sa.JSON(), nullable=False, server_default=sa.text(f"'{default_state}'")),
    )

    op.add_column(
        "extracted_product_data",
        sa.Column("is_user_edited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "extracted_product_data",
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "icp_profiles",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "icp_profiles",
        sa.Column("is_user_edited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "icp_profiles",
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "scenarios",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scenarios",
        sa.Column("is_user_edited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "scenarios",
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(f"UPDATE analyses SET workflow_state_json = '{final_state}', current_stage = 'final_review' WHERE status = 'completed'")
    op.execute(
        "UPDATE analyses SET workflow_state_json = "
        f"'{default_state}', current_stage = 'product_understanding' "
        "WHERE status IN ('queued', 'processing', 'failed')"
    )

    op.alter_column("analyses", "current_stage", server_default=None)
    op.alter_column("analyses", "workflow_state_json", server_default=None)
    op.alter_column("extracted_product_data", "is_user_edited", server_default=None)
    op.alter_column("icp_profiles", "display_order", server_default=None)
    op.alter_column("icp_profiles", "is_user_edited", server_default=None)
    op.alter_column("scenarios", "display_order", server_default=None)
    op.alter_column("scenarios", "is_user_edited", server_default=None)


def downgrade() -> None:
    op.drop_column("scenarios", "edited_at")
    op.drop_column("scenarios", "is_user_edited")
    op.drop_column("scenarios", "display_order")
    op.drop_column("icp_profiles", "edited_at")
    op.drop_column("icp_profiles", "is_user_edited")
    op.drop_column("icp_profiles", "display_order")
    op.drop_column("extracted_product_data", "edited_at")
    op.drop_column("extracted_product_data", "is_user_edited")
    op.drop_column("analyses", "workflow_state_json")
    op.drop_column("analyses", "current_stage")
