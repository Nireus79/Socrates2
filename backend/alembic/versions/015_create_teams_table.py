"""create teams table

Revision ID: 015
Revises: 014
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create teams table"""
    if not _should_run():
        return

    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Team name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Team description'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, comment='User who created the team'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when team was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when team was last updated'),
    )

    # Create indexes
    op.create_index('idx_teams_created_by', 'teams', ['created_by'])
    op.create_index('idx_teams_created_at', 'teams', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})


def downgrade():
    """Drop teams table"""
    if not _should_run():
        return

    op.drop_index('idx_teams_created_at', table_name='teams')
    op.drop_index('idx_teams_created_by', table_name='teams')
    op.drop_table('teams')
