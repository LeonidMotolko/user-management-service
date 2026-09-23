"""add user indexes for group and phone

Revision ID: 7f2c1a9b4d10
Revises: 3c109ff15c48
Create Date: 2026-09-18 01:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "7f2c1a9b4d10"
down_revision: str | Sequence[str] | None = "3c109ff15c48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_users_group_id", "users", ["group_id"], unique=False)
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_index("ix_users_group_id", table_name="users")
