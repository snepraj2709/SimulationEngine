"""Initial schema

Revision ID: 20260406_0001
Revises:
Create Date: 2026-04-06 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260406_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "analyses",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("input_url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"], unique=False)
    op.create_index("ix_analyses_user_created", "analyses", ["user_id", "created_at"], unique=False)
    op.create_index("ix_analyses_normalized_status", "analyses", ["normalized_url", "status"], unique=False)

    op.create_table(
        "extracted_product_data",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("subcategory", sa.Text(), nullable=False),
        sa.Column("positioning_summary", sa.Text(), nullable=False),
        sa.Column("pricing_model", sa.Text(), nullable=False),
        sa.Column("monetization_hypothesis", sa.Text(), nullable=False),
        sa.Column("raw_extracted_json", sa.JSON(), nullable=False),
        sa.Column("normalized_json", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id"),
    )
    op.create_index("ix_extracted_product_data_analysis_id", "extracted_product_data", ["analysis_id"], unique=True)

    op.create_table(
        "icp_profiles",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("use_case", sa.Text(), nullable=False),
        sa.Column("goals_json", sa.JSON(), nullable=False),
        sa.Column("pain_points_json", sa.JSON(), nullable=False),
        sa.Column("decision_drivers_json", sa.JSON(), nullable=False),
        sa.Column("driver_weights_json", sa.JSON(), nullable=False),
        sa.Column("price_sensitivity", sa.Float(), nullable=False),
        sa.Column("switching_cost", sa.Float(), nullable=False),
        sa.Column("alternatives_json", sa.JSON(), nullable=False),
        sa.Column("churn_threshold", sa.Float(), nullable=False),
        sa.Column("retention_threshold", sa.Float(), nullable=False),
        sa.Column("adoption_friction", sa.Float(), nullable=False),
        sa.Column("value_perception_explanation", sa.Text(), nullable=False),
        sa.Column("segment_weight", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_icp_profiles_analysis", "icp_profiles", ["analysis_id"], unique=False)

    op.create_table(
        "scenarios",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("scenario_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("input_parameters_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenarios_analysis", "scenarios", ["analysis_id"], unique=False)

    op.create_table(
        "simulation_runs",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=36), nullable=False),
        sa.Column("run_version", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("assumptions_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_runs_analysis_scenario", "simulation_runs", ["analysis_id", "scenario_id"], unique=False)

    op.create_table(
        "simulation_results",
        sa.Column("simulation_run_id", sa.String(length=36), nullable=False),
        sa.Column("icp_profile_id", sa.String(length=36), nullable=False),
        sa.Column("reaction", sa.String(length=32), nullable=False),
        sa.Column("utility_score_before", sa.Float(), nullable=False),
        sa.Column("utility_score_after", sa.Float(), nullable=False),
        sa.Column("delta_score", sa.Float(), nullable=False),
        sa.Column("revenue_delta", sa.Float(), nullable=False),
        sa.Column("perception_shift", sa.Float(), nullable=False),
        sa.Column("second_order_effects_json", sa.JSON(), nullable=False),
        sa.Column("driver_impacts_json", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["icp_profile_id"], ["icp_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["simulation_run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_results_run", "simulation_results", ["simulation_run_id"], unique=False)
    op.create_index("ix_simulation_results_icp", "simulation_results", ["icp_profile_id"], unique=False)

    op.create_table(
        "feedback_events",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=36), nullable=False),
        sa.Column("simulation_run_id", sa.String(length=36), nullable=False),
        sa.Column("feedback_type", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["simulation_run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_analysis", "feedback_events", ["analysis_id"], unique=False)
    op.create_index("ix_feedback_user_run", "feedback_events", ["user_id", "simulation_run_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_feedback_user_run", table_name="feedback_events")
    op.drop_index("ix_feedback_analysis", table_name="feedback_events")
    op.drop_table("feedback_events")
    op.drop_index("ix_simulation_results_icp", table_name="simulation_results")
    op.drop_index("ix_simulation_results_run", table_name="simulation_results")
    op.drop_table("simulation_results")
    op.drop_index("ix_simulation_runs_analysis_scenario", table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_index("ix_scenarios_analysis", table_name="scenarios")
    op.drop_table("scenarios")
    op.drop_index("ix_icp_profiles_analysis", table_name="icp_profiles")
    op.drop_table("icp_profiles")
    op.drop_index("ix_extracted_product_data_analysis_id", table_name="extracted_product_data")
    op.drop_table("extracted_product_data")
    op.drop_index("ix_analyses_normalized_status", table_name="analyses")
    op.drop_index("ix_analyses_user_created", table_name="analyses")
    op.drop_index("ix_analyses_user_id", table_name="analyses")
    op.drop_table("analyses")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
