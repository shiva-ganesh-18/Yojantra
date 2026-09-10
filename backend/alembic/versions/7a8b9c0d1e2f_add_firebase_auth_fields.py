"""add_firebase_auth_fields

Revision ID: 7a8b9c0d1e2f
Revises: 487b7be2fe28
Create Date: 2026-09-08 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '487b7be2fe28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=20),
            nullable=True
        )
        batch_op.add_column(
            sa.Column('firebase_uid', sa.String(length=128), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                'auth_provider',
                sa.String(length=50),
                nullable=False,
                server_default='phone'
            )
        )
        batch_op.add_column(
            sa.Column('avatar_url', sa.String(length=512), nullable=True)
        )
        batch_op.create_index(
            'ix_users_firebase_uid',
            ['firebase_uid'],
            unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_firebase_uid')
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('auth_provider')
        batch_op.drop_column('firebase_uid')
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=20),
            nullable=False
        )