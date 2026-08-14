"""
drop request_id add client_address

Revision ID: b7f4e1d9c2a8
Revises: dec5e3b5cb2c
Create Date: 2026-08-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7f4e1d9c2a8"
down_revision: str | None = "dec5e3b5cb2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("predictions") as batch_op:
        batch_op.drop_index(op.f("ix_predictions_request_id"))
        batch_op.drop_column("request_id")
        batch_op.add_column(
            sa.Column(
                "client_address",
                sa.String(255),
                nullable=False,
                server_default="default_address",
            )
        )
        batch_op.create_index(op.f("ix_predictions_client_address"), ["client_address"])
    with op.batch_alter_table("predictions") as batch_op:
        batch_op.alter_column("client_address", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("predictions") as batch_op:
        batch_op.drop_index(op.f("ix_predictions_client_address"))
        batch_op.drop_column("client_address")
        batch_op.add_column(
            sa.Column(
                "request_id",
                sa.String(36),
                nullable=False,
                server_default="downgraded_request_id",
            )
        )
        batch_op.create_index(op.f("ix_predictions_request_id"), ["request_id"])
    with op.batch_alter_table("predictions") as batch_op:
        batch_op.alter_column("request_id", server_default=None)
