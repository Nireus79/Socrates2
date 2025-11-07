"""create question_effectiveness table

Revision ID: 013
Revises: 012
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create question_effectiveness table"""
    if not _should_run():
        return

    op.create_table(
        'question_effectiveness',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References users(id) in socrates_auth'),
        sa.Column('question_template_id', sa.String(length=100), nullable=False, comment='Question template identifier'),
        sa.Column('role', sa.String(length=50), nullable=False, comment='User role (PM, BA, UX, etc.)'),
        sa.Column('times_asked', sa.Integer(), nullable=False, server_default='0', comment='Number of times question was asked'),
        sa.Column('times_answered_well', sa.Integer(), nullable=False, server_default='0', comment='Number of times answered well'),
        sa.Column('average_answer_length', sa.Integer(), nullable=True, comment='Average length of answers'),
        sa.Column('average_spec_extraction_count', sa.Numeric(5, 2), nullable=True, comment='Average specs extracted per answer'),
        sa.Column('effectiveness_score', sa.Numeric(3, 2), nullable=True, comment='How effective question is for this user (0.00-1.00)'),
        sa.Column('last_asked_at', sa.DateTime(timezone=True), nullable=True, comment='Last time question was asked'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when record was last updated'),
        sa.CheckConstraint('effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)', name='question_effectiveness_score_range'),
        sa.UniqueConstraint('user_id', 'question_template_id', name='question_effectiveness_unique')
    )

    # Create indexes
    op.create_index('idx_question_effectiveness_user_id', 'question_effectiveness', ['user_id'])
    op.create_index('idx_question_effectiveness_role', 'question_effectiveness', ['role'])
    op.create_index('idx_question_effectiveness_score', 'question_effectiveness', ['effectiveness_score'], postgresql_using='btree', postgresql_ops={'effectiveness_score': 'DESC'})


def downgrade():
    """Drop question_effectiveness table"""
    if not _should_run():
        return

    op.drop_index('idx_question_effectiveness_score', table_name='question_effectiveness')
    op.drop_index('idx_question_effectiveness_role', table_name='question_effectiveness')
    op.drop_index('idx_question_effectiveness_user_id', table_name='question_effectiveness')
    op.drop_table('question_effectiveness')
