"""add_institutions_and_sih_tables

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-09-08 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9c0d1e2f3a'
down_revision: Union[str, Sequence[str], None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Institutions table
    op.create_table(
        'institutions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('short_name', sa.String(length=100), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('institution_type', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('affiliation', sa.String(length=255), nullable=True),
        sa.Column('nirf_rank', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('sih_participation', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('is_nodal_center', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_institutions_name', 'institutions', ['name'])
    op.create_index('ix_institutions_code', 'institutions', ['code'], unique=True)
    op.create_index('ix_institutions_state', 'institutions', ['state'])
    op.create_index('ix_institutions_district', 'institutions', ['district'])

    # 2. Problem Statements table
    op.create_table(
        'sih_problem_statements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('ps_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=False),
        sa.Column('theme', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='Software', nullable=True),
        sa.Column('difficulty', sa.String(length=50), server_default='Medium', nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('expected_solution', sa.Text(), nullable=True),
        sa.Column('technology_bucket', sa.JSON(), nullable=True),
        sa.Column('official_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sih_problem_statements_ps_id', 'sih_problem_statements', ['ps_id'], unique=True)
    op.create_index('ix_sih_problem_statements_title', 'sih_problem_statements', ['title'])
    op.create_index('ix_sih_problem_statements_organization', 'sih_problem_statements', ['organization'])
    op.create_index('ix_sih_problem_statements_theme', 'sih_problem_statements', ['theme'])

    # 3. SIH Teams table
    op.create_table(
        'sih_teams',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('team_name', sa.String(length=200), nullable=False),
        sa.Column('institution_id', sa.Uuid(), nullable=False),
        sa.Column('leader_id', sa.Uuid(), nullable=True),
        sa.Column('problem_statement_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='forming', nullable=True),
        sa.Column('current_stage', sa.String(length=50), server_default='internal_hackathon', nullable=True),
        sa.Column('mentor_name', sa.String(length=255), nullable=True),
        sa.Column('mentor_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leader_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['problem_statement_id'], ['sih_problem_statements.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sih_teams_team_name', 'sih_teams', ['team_name'])
    op.create_index('ix_sih_teams_institution_id', 'sih_teams', ['institution_id'])
    op.create_index('ix_sih_teams_leader_id', 'sih_teams', ['leader_id'])
    op.create_index('ix_sih_teams_problem_statement_id', 'sih_teams', ['problem_statement_id'])
    op.create_index('ix_sih_teams_status', 'sih_teams', ['status'])

    # 4. SIH Team Members table
    op.create_table(
        'sih_team_members',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('team_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=100), server_default='Developer', nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['sih_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sih_team_members_team_id', 'sih_team_members', ['team_id'])
    op.create_index('ix_sih_team_members_user_id', 'sih_team_members', ['user_id'])

    # 5. SIH Submissions table
    op.create_table(
        'sih_submissions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('team_id', sa.Uuid(), nullable=False),
        sa.Column('stage', sa.String(length=50), server_default='college_internal', nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=False),
        sa.Column('tech_stack', sa.JSON(), nullable=True),
        sa.Column('repo_url', sa.String(length=500), nullable=True),
        sa.Column('presentation_url', sa.String(length=500), nullable=True),
        sa.Column('prototype_url', sa.String(length=500), nullable=True),
        sa.Column('jury_score', sa.Float(), nullable=True),
        sa.Column('evaluation_metrics', sa.JSON(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='submitted', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['sih_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sih_submissions_team_id', 'sih_submissions', ['team_id'])
    op.create_index('ix_sih_submissions_status', 'sih_submissions', ['status'])

    # 6. Institution Requests table
    op.create_table(
        'institution_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('requested_by_email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('institution_requests')
    op.drop_table('sih_submissions')
    op.drop_table('sih_team_members')
    op.drop_table('sih_teams')
    op.drop_table('sih_problem_statements')
    op.drop_table('institutions')
