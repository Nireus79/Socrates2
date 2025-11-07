"""create conflicts table

Revision ID: 008
Revises: 007
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('TECHNOLOGY', 'REQUIREMENT', 'TIMELINE', 'RESOURCE', name='conflicttype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('spec_ids', postgresql.ARRAY(sa.String(length=36)), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='conflictseverity'), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'RESOLVED', 'IGNORED', name='conflictstatus'), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('TECHNOLOGY', 'REQUIREMENT', 'TIMELINE', 'RESOURCE')", name='conflicts_type_valid'),
        sa.CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name='conflicts_severity_valid'),
        sa.CheckConstraint("status IN ('OPEN', 'RESOLVED', 'IGNORED')", name='conflicts_status_valid')
    )
    op.create_index('ix_conflicts_project_id', 'conflicts', ['project_id'])
    op.create_index('ix_conflicts_severity', 'conflicts', ['severity'])
    op.create_index('ix_conflicts_status', 'conflicts', ['status'])
    op.create_index('ix_conflicts_detected_at', 'conflicts', ['detected_at'])


def downgrade() -> None:
    op.drop_index('ix_conflicts_detected_at', table_name='conflicts')
    op.drop_index('ix_conflicts_status', table_name='conflicts')
    op.drop_index('ix_conflicts_severity', table_name='conflicts')
    op.drop_index('ix_conflicts_project_id', table_name='conflicts')
    op.drop_table('conflicts')
    op.execute('DROP TYPE conflicttype')
    op.execute('DROP TYPE conflictseverity')
    op.execute('DROP TYPE conflictstatus')
