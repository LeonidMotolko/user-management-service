"""initial migration

Revision ID: f4ec4bb45c1c
Revises:
Create Date: 2026-09-07 12:36:26.706255

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f4ec4bb45c1c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
