"""add institution telemetry columns

Revision ID: c5d8e7f9a1b2
Revises: b4b9c3a2a66a
Create Date: 2026-09-10 08:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d8e7f9a1b2'
down_revision: Union[str, Sequence[str], None] = 'b4b9c3a2a66a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('institutions', sa.Column('fund_utilization_percentage', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('institutions', sa.Column('available_lending_capacity_inr', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('institutions', sa.Column('capacity_tier', sa.String(length=50), nullable=True, server_default='UNVERIFIED'))
    op.add_column('institutions', sa.Column('gross_npa_ratio', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('institutions', sa.Column('net_npa_ratio', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('institutions', sa.Column('npa_risk_indicator', sa.String(length=50), nullable=True, server_default='UNKNOWN'))
    op.add_column('institutions', sa.Column('is_lending_halted', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('institutions', sa.Column('is_authenticated_live', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('institutions', sa.Column('telemetry_updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('institutions', 'telemetry_updated_at')
    op.drop_column('institutions', 'is_authenticated_live')
    op.drop_column('institutions', 'is_lending_halted')
    op.drop_column('institutions', 'npa_risk_indicator')
    op.drop_column('institutions', 'net_npa_ratio')
    op.drop_column('institutions', 'gross_npa_ratio')
    op.drop_column('institutions', 'capacity_tier')
    op.drop_column('institutions', 'available_lending_capacity_inr')
    op.drop_column('institutions', 'fund_utilization_percentage')
