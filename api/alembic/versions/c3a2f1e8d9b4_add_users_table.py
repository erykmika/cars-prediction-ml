"""
add users table with example user

Revision ID: c3a2f1e8d9b4
Revises: b7f4e1d9c2a8
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from passlib.context import CryptContext

from alembic import op

revision: str = "c3a2f1e8d9b4"
down_revision: str | None = "b7f4e1d9c2a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Insert example user: CARS_PREDICTION_USER / 123
    hashed_password = pwd_context.hash("123")
    op.execute(
        sa.text(
            "INSERT INTO users (username, hashed_password, is_active) "
            "VALUES (:username, :hashed_password, :is_active)"
        ).bindparams(
            username="CARS_PREDICTION_USER", hashed_password=hashed_password, is_active=True
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
