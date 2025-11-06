"""
CRITICAL PERSISTENCE TESTS

⚠️  THIS TEST FAILED IN THE ARCHIVE - Caused complete data loss!

These tests verify that data actually persists to the database after
the session closes. The previous implementation had a catastrophic bug
where sessions closed before commits synced to disk, resulting in:
- API returned 201 Created
- But database had 0 records
- Users lost ALL data

This test MUST PASS before proceeding to Phase 2.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.app.models.user import User
from backend.app.core.database import get_db_auth, engine_auth
from backend.app.core.config import settings


class TestDataPersistence:
    """
    Test that data persists after session closes.
    This is the test that FAILED in the archive.
    """

    def test_user_persists_after_session_close(self):
        """
        ⚠️  ARCHIVE KILLER BUG TEST

        Previous behavior:
        1. Create user, add to session
        2. Commit
        3. Close session
        4. Query database → 0 records found! ❌

        Expected behavior:
        1. Create user, add to session
        2. Commit
        3. Close session
        4. Query database → User found ✅
        """
        # Create user in first session
        user_id = None
        user_email = "persistence_test@example.com"

        # Session 1: Create and save user
        db = next(get_db_auth())
        try:
            # Delete any existing test user
            existing = db.query(User).filter(User.email == user_email).first()
            if existing:
                db.delete(existing)
                db.commit()

            # Create new user
            user = User(
                email=user_email,
                hashed_password=User.hash_password("test_password"),
                is_active=True,
                is_verified=False,
                status='active',
                role='user'
            )
            db.add(user)
            db.commit()

            # Extract ID BEFORE session closes
            user_id = str(user.id)
            print(f"Created user with ID: {user_id}")

        finally:
            db.close()

        # ⚠️  CRITICAL: Session 1 is now closed
        # Data MUST still be in database!

        # Session 2: Verify user exists in database
        db2 = next(get_db_auth())
        try:
            found_user = db2.query(User).filter(User.email == user_email).first()

            # ⚠️  THIS ASSERTION FAILED IN ARCHIVE
            assert found_user is not None, \
                "CRITICAL BUG: User not found after session closed! Data not persisted!"

            assert str(found_user.id) == user_id, \
                f"User ID mismatch: expected {user_id}, got {found_user.id}"

            assert found_user.email == user_email, \
                f"Email mismatch: expected {user_email}, got {found_user.email}"

            print(f"✅ SUCCESS: User persisted correctly (ID: {user_id})")

        finally:
            db2.close()

    def test_user_persists_via_dependency_injection(self):
        """
        Test persistence using FastAPI dependency injection pattern.
        This simulates how API endpoints will use the database.
        """
        user_email = "di_test@example.com"

        # Simulate API endpoint creating user
        for db in get_db_auth():
            # Delete existing test user
            existing = db.query(User).filter(User.email == user_email).first()
            if existing:
                db.delete(existing)
                # Commit happens automatically when generator exits

        # Create user using dependency injection pattern
        user_id: str = ""  # Initialize to ensure it's always defined
        for db in get_db_auth():
            user = User(
                email=user_email,
                hashed_password=User.hash_password("secure_password"),
                is_active=True,
                is_verified=True,
                status='active',
                role='user'
            )
            db.add(user)
            db.flush()  # Flush to get ID before commit
            user_id = str(user.id)
            # Commit happens automatically when generator exits

        # Verify user_id was assigned
        assert user_id, "CRITICAL: user_id was not assigned - database session may not have executed"

        # ⚠️  Session closed - verify data persisted
        for db in get_db_auth():
            found = db.query(User).filter(User.email == user_email).first()
            assert found is not None, \
                "CRITICAL: Data not persisted using dependency injection pattern!"
            assert str(found.id) == user_id, \
                f"CRITICAL: User ID mismatch - expected {user_id}, got {found.id}"
            print(f"✅ DI pattern works correctly (ID: {user_id})")

    def test_multiple_users_persist(self):
        """
        Test that multiple users all persist correctly.
        In archive, ALL records were lost.
        """
        test_emails = [
            "user1@test.com",
            "user2@test.com",
            "user3@test.com",
        ]
        created_ids = []

        # Clean up existing test users
        for db in get_db_auth():
            for email in test_emails:
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    db.delete(existing)

        # Create multiple users
        for email in test_emails:
            for db in get_db_auth():
                user = User(
                    email=email,
                    hashed_password=User.hash_password("password123"),
                    is_active=True,
                    is_verified=False,
                    status='active',
                    role='user'
                )
                db.add(user)
                db.flush()  # CRITICAL: Flush to get ID before commit
                created_ids.append(str(user.id))

        # Verify created_ids were actually assigned
        assert len(created_ids) == len(test_emails), \
            f"CRITICAL: Expected {len(test_emails)} IDs, got {len(created_ids)}"
        assert all(id_str for id_str in created_ids), \
            "CRITICAL: Some user IDs are empty or None"

        # Verify ALL users persisted with correct IDs
        for db in get_db_auth():
            for idx, email in enumerate(test_emails):
                found = db.query(User).filter(User.email == email).first()
                assert found is not None, \
                    f"CRITICAL: User {email} not persisted!"

                # Verify ID matches what we created
                expected_id = created_ids[idx]
                assert str(found.id) == expected_id, \
                    f"CRITICAL: User {email} ID mismatch - expected {expected_id}, got {found.id}"

            # Count total users created
            count = db.query(User).filter(User.email.in_(test_emails)).count()
            assert count == len(test_emails), \
                f"Expected {len(test_emails)} users, found {count}"

        print(f"✅ All {len(test_emails)} users persisted correctly with matching IDs")

    def test_raw_sql_confirms_persistence(self):
        """
        Use raw SQL to verify data is actually in PostgreSQL.
        This eliminates any ORM caching as a potential false positive.
        """
        user_email = "raw_sql_test@example.com"

        # Create user using ORM
        for db in get_db_auth():
            existing = db.query(User).filter(User.email == user_email).first()
            if existing:
                db.delete(existing)

        user_id: str = ""
        for db in get_db_auth():
            user = User(
                email=user_email,
                hashed_password=User.hash_password("test123"),
                is_active=True,
                is_verified=False,
                status='active',
                role='user'
            )
            db.add(user)
            db.flush()  # Get ID before commit
            user_id = str(user.id)

        # Verify user_id was assigned
        assert user_id, "CRITICAL: user_id was not assigned"

        # Query using raw SQL (bypasses ORM cache)
        engine = create_engine(settings.DATABASE_URL_AUTH)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, email FROM users WHERE email = :email"),
                {"email": user_email}
            )
            row = result.fetchone()

            assert row is not None, \
                "CRITICAL: User not found in database using raw SQL! ORM cache hiding the bug?"

            assert str(row[0]) == user_id, \
                f"CRITICAL: ID mismatch in raw SQL - expected {user_id}, got {row[0]}"

            assert row[1] == user_email, \
                f"Email mismatch in raw SQL: expected {user_email}, got {row[1]}"

        print(f"✅ Raw SQL confirms data persisted correctly with matching ID {user_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
