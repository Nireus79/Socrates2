"""
Verify no cross-contamination between databases
This test ensures migrations didn't create tables in wrong databases
"""

import pytest
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_AUTH = os.getenv("DATABASE_URL_AUTH")
DATABASE_URL_SPECS = os.getenv("DATABASE_URL_SPECS")


class TestNoCrossContamination:
    """Verify tables are ONLY in their correct databases"""

    def test_auth_has_only_auth_tables(self):
        """Verify socrates_auth has ONLY auth tables, no specs tables"""
        engine = create_engine(DATABASE_URL_AUTH)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        # Expected tables in socrates_auth
        expected_tables = {"users", "refresh_tokens", "alembic_version"}

        # Tables that should NOT be in socrates_auth
        forbidden_tables = {"projects", "sessions"}

        # Check expected tables exist
        for table in expected_tables:
            assert table in tables, f"Missing expected table: {table}"

        # Check forbidden tables DON'T exist
        for table in forbidden_tables:
            assert table not in tables, \
                f"CONTAMINATION: Table '{table}' found in socrates_auth (should only be in socrates_specs)"

        # Check no extra tables
        extra_tables = tables - expected_tables
        assert len(extra_tables) == 0, \
            f"Unexpected tables in socrates_auth: {extra_tables}"

        engine.dispose()

    def test_specs_has_only_specs_tables(self):
        """Verify socrates_specs has ONLY specs tables, no auth tables"""
        engine = create_engine(DATABASE_URL_SPECS)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        # Expected tables in socrates_specs
        expected_tables = {"projects", "sessions", "alembic_version"}

        # Tables that should NOT be in socrates_specs
        forbidden_tables = {"users", "refresh_tokens"}

        # Check expected tables exist
        for table in expected_tables:
            assert table in tables, f"Missing expected table: {table}"

        # Check forbidden tables DON'T exist
        for table in forbidden_tables:
            assert table not in tables, \
                f"CONTAMINATION: Table '{table}' found in socrates_specs (should only be in socrates_auth)"

        # Check no extra tables
        extra_tables = tables - expected_tables
        assert len(extra_tables) == 0, \
            f"Unexpected tables in socrates_specs: {extra_tables}"

        engine.dispose()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
