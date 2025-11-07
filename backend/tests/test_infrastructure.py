"""
Infrastructure Tests - Database Connections, Schema, Migrations

Tests verify:
- Database connections work
- Both databases exist
- All tables created correctly
- Foreign keys working
- Indexes exist
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URLs from .env
DATABASE_URL_AUTH = os.getenv("DATABASE_URL_AUTH")
DATABASE_URL_SPECS = os.getenv("DATABASE_URL_SPECS")


class TestDatabaseConnections:
    """Test that both databases are accessible"""

    def test_auth_database_connection(self):
        """Test connection to socrates_auth database"""
        engine = create_engine(DATABASE_URL_AUTH)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except OperationalError as e:
            pytest.fail(f"Failed to connect to auth database: {e}")
        finally:
            engine.dispose()

    def test_specs_database_connection(self):
        """Test connection to socrates_specs database"""
        engine = create_engine(DATABASE_URL_SPECS)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except OperationalError as e:
            pytest.fail(f"Failed to connect to specs database: {e}")
        finally:
            engine.dispose()


class TestAuthDatabaseSchema:
    """Test socrates_auth database schema"""

    @pytest.fixture(scope="class")
    def auth_inspector(self):
        """Create SQLAlchemy inspector for auth database"""
        engine = create_engine(DATABASE_URL_AUTH)
        inspector = inspect(engine)
        yield inspector
        engine.dispose()

    def test_auth_tables_exist(self, auth_inspector):
        """Test that required tables exist in socrates_auth"""
        tables = auth_inspector.get_table_names()

        required_tables = ["users", "refresh_tokens", "alembic_version"]

        for table in required_tables:
            assert table in tables, f"Table '{table}' not found in socrates_auth"

    def test_users_table_columns(self, auth_inspector):
        """Test users table has correct columns"""
        columns = {col["name"]: col for col in auth_inspector.get_columns("users")}

        required_columns = [
            "id", "email", "hashed_password", "is_active",
            "is_verified", "status", "role", "created_at", "updated_at"
        ]

        for col in required_columns:
            assert col in columns, f"Column '{col}' not found in users table"

        # Check email is unique
        indexes = auth_inspector.get_indexes("users")
        unique_cols = [idx["column_names"] for idx in indexes if idx.get("unique")]
        assert any("email" in cols for cols in unique_cols), "email column should have unique index"

    def test_refresh_tokens_table_columns(self, auth_inspector):
        """Test refresh_tokens table has correct columns"""
        columns = {col["name"]: col for col in auth_inspector.get_columns("refresh_tokens")}

        required_columns = [
            "id", "user_id", "token", "expires_at", "is_revoked", "created_at"
        ]

        for col in required_columns:
            assert col in columns, f"Column '{col}' not found in refresh_tokens table"

    def test_refresh_tokens_foreign_key(self, auth_inspector):
        """Test refresh_tokens has foreign key to users"""
        foreign_keys = auth_inspector.get_foreign_keys("refresh_tokens")

        assert len(foreign_keys) > 0, "refresh_tokens should have foreign key constraint"

        # Check foreign key points to users table
        fk = foreign_keys[0]
        assert fk["referred_table"] == "users", "Foreign key should reference users table"
        assert "user_id" in fk["constrained_columns"], "Foreign key should be on user_id column"

    def test_users_indexes_exist(self, auth_inspector):
        """Test users table has required indexes"""
        indexes = auth_inspector.get_indexes("users")
        index_columns = [idx["column_names"] for idx in indexes]

        # Should have indexes on email, is_active, status
        assert any("email" in cols for cols in index_columns), "Missing index on email"
        # Note: Some indexes might be on multiple columns, so we check if the column appears


class TestSpecsDatabaseSchema:
    """Test socrates_specs database schema"""

    @pytest.fixture(scope="class")
    def specs_inspector(self):
        """Create SQLAlchemy inspector for specs database"""
        engine = create_engine(DATABASE_URL_SPECS)
        inspector = inspect(engine)
        yield inspector
        engine.dispose()

    def test_specs_tables_exist(self, specs_inspector):
        """Test that required tables exist in socrates_specs"""
        tables = specs_inspector.get_table_names()

        required_tables = ["projects", "sessions", "alembic_version"]

        for table in required_tables:
            assert table in tables, f"Table '{table}' not found in socrates_specs"

    def test_projects_table_columns(self, specs_inspector):
        """Test projects table has correct columns"""
        columns = {col["name"]: col for col in specs_inspector.get_columns("projects")}

        required_columns = [
            "id", "user_id", "name", "description", "current_phase",
            "maturity_score", "status", "created_at", "updated_at"
        ]

        for col in required_columns:
            assert col in columns, f"Column '{col}' not found in projects table"

    def test_sessions_table_columns(self, specs_inspector):
        """Test sessions table has correct columns"""
        columns = {col["name"]: col for col in specs_inspector.get_columns("sessions")}

        required_columns = [
            "id", "project_id", "mode", "status",
            "started_at", "ended_at", "created_at", "updated_at"
        ]

        for col in required_columns:
            assert col in columns, f"Column '{col}' not found in sessions table"

    def test_sessions_foreign_key(self, specs_inspector):
        """Test sessions has foreign key to projects"""
        foreign_keys = specs_inspector.get_foreign_keys("sessions")

        assert len(foreign_keys) > 0, "sessions should have foreign key constraint"

        # Check foreign key points to projects table
        fk = foreign_keys[0]
        assert fk["referred_table"] == "projects", "Foreign key should reference projects table"
        assert "project_id" in fk["constrained_columns"], "Foreign key should be on project_id column"

    def test_projects_check_constraint(self, specs_inspector):
        """Test projects table has check constraint on maturity_score"""
        # Note: Getting check constraints varies by database
        # This is a basic test that the constraint exists
        check_constraints = specs_inspector.get_check_constraints("projects")

        # Should have constraint on maturity_score (0-100)
        assert len(check_constraints) > 0, "projects should have check constraint on maturity_score"


class TestCrossDatabase:
    """Test that databases are properly separated"""

    def test_no_cross_database_foreign_keys(self):
        """Test that projects.user_id does NOT have FK constraint to users table

        This is correct behavior - cross-database FKs not supported in PostgreSQL.
        user_id is a reference but not enforced by database constraint.
        """
        engine = create_engine(DATABASE_URL_SPECS)
        inspector = inspect(engine)

        foreign_keys = inspector.get_foreign_keys("projects")

        # Should NOT have foreign key to users (different database)
        for fk in foreign_keys:
            assert fk["referred_table"] != "users", \
                "projects should NOT have FK constraint to users (cross-database)"

        engine.dispose()


class TestMigrationState:
    """Test Alembic migration tracking"""

    def test_auth_alembic_version(self):
        """Test that socrates_auth has Alembic version tracked

        Note: Both databases will show version 004 if all migrations were run
        via 'alembic upgrade head', even though migrations 003-004 didn't
        create tables in socrates_auth. This is normal Alembic behavior.
        """
        engine = create_engine(DATABASE_URL_AUTH)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            # Should be at migration 007 (Phase 1: 001-004, Phase 2: 005-007)
            assert version == "007", \
                f"Expected migration 007, got {version}"

        engine.dispose()

    def test_specs_alembic_version(self):
        """Test that socrates_specs has correct Alembic version"""
        engine = create_engine(DATABASE_URL_SPECS)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            # Should be at migration 019 (Phase 1: 001-004, Phase 2: 005-007, Phase 3: 008, Phase 4: 009-010, Phase 5: 011, Phase 6: 012-014, Phase 8: 015-017, Phase 9: 018-019)
            assert version == "019", f"Expected migration 019, got {version}"

        engine.dispose()


class TestDatabaseOperations:
    """Test basic CRUD operations work"""

    @pytest.fixture(scope="class")
    def auth_engine(self):
        """Create engine for auth database"""
        engine = create_engine(DATABASE_URL_AUTH)
        yield engine
        engine.dispose()

    @pytest.fixture(scope="class")
    def specs_engine(self):
        """Create engine for specs database"""
        engine = create_engine(DATABASE_URL_SPECS)
        yield engine
        engine.dispose()

    def test_can_insert_user(self, auth_engine):
        """Test that we can insert a user into users table"""
        with auth_engine.connect() as conn:
            # Insert test user
            result = conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, is_active, is_verified, status, role)
                    VALUES (:email, :password, true, false, 'active', 'user')
                    RETURNING id
                """),
                {"email": "test_infra@example.com", "password": "hashed_password_here"}
            )
            user_id = result.scalar()
            conn.commit()

            assert user_id is not None, "Should return user ID after insert"

            # Clean up
            conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": "test_infra@example.com"})
            conn.commit()

    def test_can_insert_project(self, specs_engine):
        """Test that we can insert a project into projects table"""
        with specs_engine.connect() as conn:
            # Insert test project (user_id can be any UUID - no FK constraint)
            result = conn.execute(
                text("""
                    INSERT INTO projects (user_id, name, description, current_phase, maturity_score, status)
                    VALUES (gen_random_uuid(), :name, :desc, 'discovery', 50, 'active')
                    RETURNING id
                """),
                {"name": "Test Project", "desc": "Infrastructure test"}
            )
            project_id = result.scalar()
            conn.commit()

            assert project_id is not None, "Should return project ID after insert"

            # Clean up
            conn.execute(text("DELETE FROM projects WHERE name = :name"), {"name": "Test Project"})
            conn.commit()

    def test_cascade_delete_sessions(self, specs_engine):
        """Test that deleting a project cascades to sessions"""
        with specs_engine.connect() as conn:
            # Insert test project
            result = conn.execute(
                text("""
                    INSERT INTO projects (user_id, name, current_phase, maturity_score, status)
                    VALUES (gen_random_uuid(), 'Cascade Test', 'discovery', 0, 'active')
                    RETURNING id
                """)
            )
            project_id = result.scalar()
            conn.commit()

            # Insert session for this project
            conn.execute(
                text("""
                    INSERT INTO sessions (project_id, mode, status)
                    VALUES (:project_id, 'socratic', 'active')
                """),
                {"project_id": project_id}
            )
            conn.commit()

            # Verify session exists
            result = conn.execute(
                text("SELECT COUNT(*) FROM sessions WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            assert result.scalar() == 1, "Session should exist"

            # Delete project - should cascade to sessions
            conn.execute(
                text("DELETE FROM projects WHERE id = :project_id"),
                {"project_id": project_id}
            )
            conn.commit()

            # Verify session was deleted via CASCADE
            result = conn.execute(
                text("SELECT COUNT(*) FROM sessions WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            assert result.scalar() == 0, "Session should be deleted via CASCADE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
