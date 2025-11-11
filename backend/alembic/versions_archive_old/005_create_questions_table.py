"""Create questions table

Revision ID: 005
Revises: 004
Create Date: 2025-11-06

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    if not _should_run():
        return

    op.create_table(
        'questions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Numeric(3, 2), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign keys
    op.create_foreign_key(
        'fk_questions_project_id',
        'questions', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_questions_session_id',
        'questions', 'sessions',
        ['session_id'], ['id'],
        ondelete='CASCADE'
    )

    # Indexes
    op.create_index('idx_questions_project_id', 'questions', ['project_id'])
    op.create_index('idx_questions_session_id', 'questions', ['session_id'])
    op.create_index('idx_questions_category', 'questions', ['category'])
    op.create_index('idx_questions_created_at', 'questions', ['created_at'])

    # Check constraint
    op.create_check_constraint(
        'check_questions_quality_score_valid',
        'questions',
        'quality_score >= 0.00 AND quality_score <= 1.00'
    )


def downgrade():
    if not _should_run():
        return

    op.drop_constraint('check_questions_quality_score_valid', 'questions', type_='check')
    op.drop_index('idx_questions_created_at')
    op.drop_index('idx_questions_category')
    op.drop_index('idx_questions_session_id')
    op.drop_index('idx_questions_project_id')
    op.drop_constraint('fk_questions_session_id', 'questions', type_='foreignkey')
    op.drop_constraint('fk_questions_project_id', 'questions', type_='foreignkey')
    op.drop_table('questions')
