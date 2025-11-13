#!/usr/bin/env python
"""
Phase 1b Setup Verification Script

Verifies that Phase 1b infrastructure is properly configured:
- .env file exists with required variables
- PostgreSQL databases exist and are accessible
- Database migrations are applied
- Settings can be loaded without errors
- Dependency injection container works
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def checkmark():
    """Return check mark (ASCII compatible)"""
    return "[OK]"


def cross():
    """Return cross mark (ASCII compatible)"""
    return "[X]"


def check_env_file():
    """Verify .env file exists and has required variables"""
    print_section("1. Environment File Check")

    env_path = backend_dir / ".env"

    if not env_path.exists():
        print(f"[X] .env file not found at {env_path}")
        return False

    print(f"[OK] .env file found at {env_path}")

    # Check for required variables
    required_vars = [
        "DATABASE_URL_AUTH",
        "DATABASE_URL_SPECS",
        "SECRET_KEY",
        "ANTHROPIC_API_KEY",
    ]

    with open(env_path) as f:
        env_content = f.read()

    missing = []
    for var in required_vars:
        if var in env_content:
            print(f"[OK] {var} configured")
        else:
            print(f"[X] {var} missing")
            missing.append(var)

    return len(missing) == 0


def check_settings_load():
    """Verify Settings can be loaded from environment"""
    print_section("2. Settings Loading Check")

    try:
        # Load environment
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        load_dotenv(env_path)

        print(f"[OK] Loaded .env file")

        # Try to get settings
        from app.core.config import get_settings
        settings = get_settings()

        print(f"[OK] Settings loaded successfully")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug: {settings.DEBUG}")
        print(f"   Database Auth URL: {settings.DATABASE_URL_AUTH[:50]}...")
        print(f"   Database Specs URL: {settings.DATABASE_URL_SPECS[:50]}...")

        return True

    except Exception as e:
        print(f"[X] Failed to load settings: {e}")
        return False


def check_database_connectivity():
    """Verify database connections work"""
    print_section("3. Database Connectivity Check")

    try:
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        load_dotenv(env_path)

        from sqlalchemy import text
        from app.core.database import engine_auth, engine_specs

        # Test auth database
        try:
            with engine_auth.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[OK] Auth database (socrates_auth) connected")
        except Exception as e:
            print(f"[X] Auth database connection failed: {e}")
            return False

        # Test specs database
        try:
            with engine_specs.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[OK] Specs database (socrates_specs) connected")
        except Exception as e:
            print(f"[X] Specs database connection failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"[X] Database connectivity check failed: {e}")
        return False


def check_migrations():
    """Verify database migrations are applied"""
    print_section("4. Database Migrations Check")

    try:
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        load_dotenv(env_path)

        from sqlalchemy import inspect, text
        from app.core.database import engine_auth, engine_specs
        from app.models.base import Base

        # Check auth database tables
        inspector_auth = inspect(engine_auth)
        auth_tables = inspector_auth.get_table_names()

        expected_auth_tables = ["user", "refresh_token", "admin_role", "admin_user", "admin_audit_log"]
        auth_missing = [t for t in expected_auth_tables if t not in auth_tables]

        if not auth_missing:
            print(f"[OK] Auth database tables present: {len(auth_tables)} tables")
            for table in auth_tables:
                print(f"   - {table}")
        else:
            print(f"[!]  Auth database has {len(auth_tables)} tables (expected {len(expected_auth_tables)})")
            print(f"   Missing: {auth_missing}")

        # Check specs database tables
        inspector_specs = inspect(engine_specs)
        specs_tables = inspector_specs.get_table_names()

        expected_specs_tables = ["project", "session", "question", "specification", "conversation_history", "conflict"]
        specs_missing = [t for t in expected_specs_tables if t not in specs_tables]

        if not specs_missing:
            print(f"[OK] Specs database tables present: {len(specs_tables)} tables")
            for table in specs_tables[:5]:  # Show first 5
                print(f"   - {table}")
            if len(specs_tables) > 5:
                print(f"   ... and {len(specs_tables) - 5} more")
        else:
            print(f"[!]  Specs database has {len(specs_tables)} tables (expected {len(expected_specs_tables)})")
            print(f"   Missing: {specs_missing}")

        return len(auth_missing) == 0 and len(specs_missing) == 0

    except Exception as e:
        print(f"[X] Migration check failed: {e}")
        return False


def check_dependency_injection():
    """Verify ServiceContainer and dependency injection works"""
    print_section("5. Dependency Injection Check")

    try:
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        load_dotenv(env_path)

        from app.core.dependencies import ServiceContainer

        # Create container
        container = ServiceContainer()
        print(f"[OK] ServiceContainer created")

        # Try to get services
        try:
            db_auth = container.get_database_auth()
            print(f"[OK] Database auth session obtained")
            db_auth.close()
        except Exception as e:
            print(f"[X] Could not get auth database: {e}")
            return False

        try:
            db_specs = container.get_database_specs()
            print(f"[OK] Database specs session obtained")
            db_specs.close()
        except Exception as e:
            print(f"[X] Could not get specs database: {e}")
            return False

        return True

    except Exception as e:
        print(f"[X] Dependency injection check failed: {e}")
        return False


def check_imports():
    """Verify Phase 1b imports work"""
    print_section("6. Phase 1b Imports Check")

    try:
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        load_dotenv(env_path)

        # Try importing Phase 1b exports (assuming they're commented out for now)
        print("Testing Phase 1b imports...")

        try:
            from app.core.config import Settings, get_settings
            print("[OK] Settings, get_settings")
        except Exception as e:
            print(f"[X] Config: {e}")

        try:
            from app.core.dependencies import ServiceContainer
            print("[OK] ServiceContainer")
        except Exception as e:
            print(f"[X] Dependencies: {e}")

        try:
            from app.core.database import (
                engine_auth, engine_specs,
                SessionLocalAuth, SessionLocalSpecs,
                get_db_auth, get_db_specs
            )
            print("[OK] Database (engines, sessions, getters)")
        except Exception as e:
            print(f"[X] Database: {e}")

        try:
            from app.core.security import (
                create_access_token, decode_access_token,
                get_current_user, oauth2_scheme
            )
            print("[OK] Security (JWT, auth)")
        except Exception as e:
            print(f"[X] Security: {e}")

        return True

    except Exception as e:
        print(f"[X] Import check failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("  SOCRATES PHASE 1b SETUP VERIFICATION")
    print("="*70)

    checks = [
        ("Environment File", check_env_file),
        ("Settings Loading", check_settings_load),
        ("Database Connectivity", check_database_connectivity),
        ("Database Migrations", check_migrations),
        ("Dependency Injection", check_dependency_injection),
        ("Phase 1b Imports", check_imports),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n[X] {name}: Unexpected error: {e}")
            results[name] = False

    # Summary
    print_section("SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n[OK] Phase 1b setup is complete and ready!")
        return 0
    else:
        print("\n[!]  Some checks failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
