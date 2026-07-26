"""
add predictions table

Revision ID: dec5e3b5cb2c
Revises:
Create Date: 2026-07-24 20:01:36.784993
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "dec5e3b5cb2c"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("prediction", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index(op.f("ix_predictions_request_id"), "predictions", ["request_id"])
    op.create_index(op.f("ix_predictions_created_at"), "predictions", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_predictions_created_at"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_request_id"), table_name="predictions")
    op.drop_table("predictions")
