"""increase avatar url length

Revision ID: b4b9c3a2a66a
Revises: 8b9c0d1e2f3a
Create Date: 2026-09-09 00:12:05.421553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4b9c3a2a66a'
down_revision: Union[str, Sequence[str], None] = '8b9c0d1e2f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
