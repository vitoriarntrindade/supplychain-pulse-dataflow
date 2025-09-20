"""init schema

Revision ID: 453d3b18f6fc
Revises:
Create Date: 2025-09-18 13:41:45.884146

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "453d3b18f6fc"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
