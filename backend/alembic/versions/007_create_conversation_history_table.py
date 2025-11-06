"""Create conversation_history table

Revision ID: 007
Revises: 006
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key
    op.create_foreign_key(
        'fk_conversation_history_session_id',
        'conversation_history', 'sessions',
        ['session_id'], ['id'],
        ondelete='CASCADE'
    )

    # Indexes
    op.create_index('idx_conversation_history_session_id', 'conversation_history', ['session_id'])
    op.create_index('idx_conversation_history_timestamp', 'conversation_history', ['timestamp'])

    # Check constraint
    op.create_check_constraint(
        'check_conversation_history_role_valid',
        'conversation_history',
        "role IN ('user', 'assistant', 'system')"
    )

def downgrade():
    op.drop_constraint('check_conversation_history_role_valid', 'conversation_history', type_='check')
    op.drop_index('idx_conversation_history_timestamp')
    op.drop_index('idx_conversation_history_session_id')
    op.drop_constraint('fk_conversation_history_session_id', 'conversation_history', type_='foreignkey')
    op.drop_table('conversation_history')
