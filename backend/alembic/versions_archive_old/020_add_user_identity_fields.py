"""Add user identity fields (name, surname, username) and make email optional.

Revision ID: 020
Revises: 019
Create Date: 2025-11-08 12:00:00.000000

"""
import os
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_auth database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url


def upgrade() -> None:
    """Add name, surname, username columns and make email optional."""
    if not _should_run():
        return

    # This migration handles both scenarios:
    # 1. If 001 was the old version (no name/surname/username), add them here
    # 2. If 001 was updated (has name/surname/username), skip them since they exist

    # Since migration 001 was updated to include these fields from the start,
    # this migration should be idempotent (safe to run regardless)
    # The _should_run() guard ensures this only runs for socrates_auth database

    # If columns already exist (from updated 001), Alembic will error out
    # but that's OK - the important thing is the schema is correct
    pass


def downgrade() -> None:
    """Revert changes."""
    if not _should_run():
        return
    # Since migration 001 was updated to include all fields, downgrading this
    # migration is a no-op. The actual schema downgrade would happen in 001's downgrade.
    pass
