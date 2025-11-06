"""Create specifications table

Revision ID: 006
Revises: 005
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'specifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('spec_metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('superseded_at', sa.DateTime(), nullable=True),
        sa.Column('superseded_by', UUID(as_uuid=True), nullable=True)
    )

    # Foreign keys
    op.create_foreign_key(
        'fk_specifications_project_id',
        'specifications', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_specifications_session_id',
        'specifications', 'sessions',
        ['session_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_specifications_superseded_by',
        'specifications', 'specifications',
        ['superseded_by'], ['id'],
        ondelete='SET NULL'
    )

    # Indexes
    op.create_index('idx_specifications_project_id', 'specifications', ['project_id'])
    op.create_index('idx_specifications_category', 'specifications', ['category'])
    op.create_index(
        'idx_specifications_is_current',
        'specifications',
        ['is_current'],
        postgresql_where=sa.text('is_current = true')
    )
    op.create_index('idx_specifications_created_at', 'specifications', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})

    # Check constraint
    op.create_check_constraint(
        'check_specifications_confidence_range',
        'specifications',
        'confidence IS NULL OR (confidence >= 0 AND confidence <= 1)'
    )

def downgrade():
    op.drop_constraint('check_specifications_confidence_range', 'specifications', type_='check')
    op.drop_index('idx_specifications_created_at')
    op.drop_index('idx_specifications_is_current')
    op.drop_index('idx_specifications_category')
    op.drop_index('idx_specifications_project_id')
    op.drop_constraint('fk_specifications_superseded_by', 'specifications', type_='foreignkey')
    op.drop_constraint('fk_specifications_session_id', 'specifications', type_='foreignkey')
    op.drop_constraint('fk_specifications_project_id', 'specifications', type_='foreignkey')
    op.drop_table('specifications')
