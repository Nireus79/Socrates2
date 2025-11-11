"""create user_behavior_patterns table

Revision ID: 012
Revises: 011
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create user_behavior_patterns table"""
    if not _should_run():
        return

    op.create_table(
        'user_behavior_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References users(id) in socrates_auth'),
        sa.Column('pattern_type', sa.String(length=50), nullable=False, comment='Pattern type (e.g., communication_style, detail_level)'),
        sa.Column('pattern_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Pattern data as JSON'),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False, comment='Confidence score (0.00-1.00)'),
        sa.Column('learned_from_projects', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True, comment='Array of project IDs where pattern was learned'),
        sa.Column('learned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when pattern was learned'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when pattern was last updated'),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='user_behavior_patterns_confidence_range')
    )

    # Create indexes
    op.create_index('idx_user_behavior_patterns_user_id', 'user_behavior_patterns', ['user_id'])
    op.create_index('idx_user_behavior_patterns_type', 'user_behavior_patterns', ['pattern_type'])
    op.create_index('idx_user_behavior_patterns_confidence', 'user_behavior_patterns', ['confidence'], postgresql_using='btree', postgresql_ops={'confidence': 'DESC'})


def downgrade():
    """Drop user_behavior_patterns table"""
    if not _should_run():
        return

    op.drop_index('idx_user_behavior_patterns_confidence', table_name='user_behavior_patterns')
    op.drop_index('idx_user_behavior_patterns_type', table_name='user_behavior_patterns')
    op.drop_index('idx_user_behavior_patterns_user_id', table_name='user_behavior_patterns')
    op.drop_table('user_behavior_patterns')
