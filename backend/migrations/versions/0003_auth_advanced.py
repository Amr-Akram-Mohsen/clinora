"""Add email verification, password reset, and google_id to users

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("verification_token", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(255), nullable=True),
    )

    op.create_index("ix_users_verification_token", "users", ["verification_token"])
    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"])
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    # For existing users (like seeded admin), mark them verified
    op.execute("UPDATE users SET is_verified = true WHERE is_superuser = true")


def downgrade() -> None:
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_index("ix_users_password_reset_token", table_name="users")
    op.drop_index("ix_users_verification_token", table_name="users")
    op.drop_column("users", "google_id")
    op.drop_column("users", "password_reset_sent_at")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "verification_expires_at")
    op.drop_column("users", "verification_token")
    op.drop_column("users", "is_verified")
