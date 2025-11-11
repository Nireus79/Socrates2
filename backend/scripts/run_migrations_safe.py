#!/usr/bin/env python
"""
Safe Migration Runner for Socrates2

Handles running migrations for both databases (socrates_auth and socrates_specs)
with proper error handling and rollback capabilities.

Usage:
    python scripts/run_migrations_safe.py
    python scripts/run_migrations_safe.py --auth-only
    python scripts/run_migrations_safe.py --specs-only
    python scripts/run_migrations_safe.py --rollback
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# Add parent directory to path so we can import from app
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings


class MigrationRunner:
    """Manages database migrations for both socrates_auth and socrates_specs"""

    def __init__(self):
        self.backend_dir = BACKEND_DIR
        self.auth_db_url = settings.DATABASE_URL_AUTH
        self.specs_db_url = settings.DATABASE_URL_SPECS
        self.alembic_dir = self.backend_dir / "alembic"

    def run_command(self, cmd: list, env: Optional[dict] = None) -> Tuple[int, str, str]:
        """Run a shell command and capture output"""
        try:
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            result = subprocess.run(
                cmd,
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
                env=process_env,
                timeout=120
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Migration timeout (exceeded 120 seconds)"
        except Exception as e:
            return 1, "", str(e)

    def migrate_database(self, db_name: str, db_url: str, target: str = "head", branch: str = None) -> bool:
        """
        Run migrations for a specific database

        Args:
            db_name: Name of database (socrates_auth or socrates_specs)
            db_url: Database URL
            target: Migration target revision (default: head)
            branch: Branch label for multi-database migrations (auth or specs)

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Running migrations for: {db_name}")
        print(f"Database URL: {db_url}")
        if branch:
            print(f"Branch: {branch}")
        print(f"Target: {target}")
        print(f"{'='*70}\n", flush=True)

        # Use branch-specific target if branch is specified
        if branch:
            target = f"{branch}@{target}"

        cmd = ["alembic", "upgrade", target]
        env = {"DATABASE_URL": db_url}

        returncode, stdout, stderr = self.run_command(cmd, env)

        # Print output
        if stdout:
            print("STDOUT:")
            print(stdout)

        if stderr:
            print("STDERR:")
            print(stderr)

        if returncode == 0:
            print(f"[SUCCESS] Successfully migrated {db_name}")
            return True
        else:
            print(f"[FAILED] Failed to migrate {db_name}")
            return False

    def get_current_version(self, db_name: str, db_url: str) -> Optional[str]:
        """Get the current migration version for a database"""
        cmd = ["alembic", "current"]
        env = {"DATABASE_URL": db_url}
        returncode, stdout, _ = self.run_command(cmd, env)

        if returncode == 0 and stdout.strip():
            return stdout.strip().split('\n')[0].strip()
        return None

    def run_all_migrations(self) -> bool:
        """Run migrations for both databases"""
        print("\n" + "="*70)
        print("SOCRATES2 MIGRATION RUNNER - Running All Migrations")
        print("="*70)

        # Migrate auth database first (smaller, user/admin tables)
        auth_success = self.migrate_database(
            "socrates_auth",
            self.auth_db_url,
            "head",
            branch="auth"
        )

        if not auth_success:
            print("\n⚠️  Auth database migration failed. Aborting specs migrations.")
            return False

        # Migrate specs database (larger, project/specification tables)
        specs_success = self.migrate_database(
            "socrates_specs",
            self.specs_db_url,
            "head",
            branch="specs"
        )

        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"socrates_auth: {'[SUCCESS]' if auth_success else '[FAILED]'}")
        print(f"socrates_specs: {'[SUCCESS]' if specs_success else '[FAILED]'}")

        # Check current versions
        auth_version = self.get_current_version("socrates_auth", self.auth_db_url)
        specs_version = self.get_current_version("socrates_specs", self.specs_db_url)

        print(f"\nCurrent Versions:")
        print(f"  socrates_auth: {auth_version or 'unknown'}")
        print(f"  socrates_specs: {specs_version or 'unknown'}")

        return auth_success and specs_success

    def run_auth_only(self) -> bool:
        """Run migrations only for auth database"""
        return self.migrate_database("socrates_auth", self.auth_db_url, "head", branch="auth")

    def run_specs_only(self) -> bool:
        """Run migrations only for specs database"""
        return self.migrate_database("socrates_specs", self.specs_db_url, "head", branch="specs")

    def rollback_all(self) -> bool:
        """Rollback all migrations (use with caution!)"""
        print("\n⚠️  WARNING: This will rollback ALL migrations!")
        response = input("Continue? (yes/no): ").lower()

        if response != "yes":
            print("Rollback cancelled")
            return False

        print("\nRolling back socrates_auth...")
        self.migrate_database("socrates_auth", self.auth_db_url, "base")

        print("\nRolling back socrates_specs...")
        self.migrate_database("socrates_specs", self.specs_db_url, "base")

        return True

    def validate_config(self) -> bool:
        """Validate database configuration"""
        print("\nValidating configuration...")

        if not self.auth_db_url:
            print("[ERROR] DATABASE_URL_AUTH not set")
            return False

        if not self.specs_db_url:
            print("[ERROR] DATABASE_URL_SPECS not set")
            return False

        if not self.alembic_dir.exists():
            print(f"[ERROR] Alembic directory not found: {self.alembic_dir}")
            return False

        print("[OK] Configuration valid")
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Safe migration runner for Socrates2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_migrations_safe.py              # Run all migrations
  python scripts/run_migrations_safe.py --auth-only  # Auth database only
  python scripts/run_migrations_safe.py --specs-only # Specs database only
  python scripts/run_migrations_safe.py --rollback   # Rollback all (careful!)
        """
    )

    parser.add_argument("--auth-only", action="store_true", help="Run auth database migrations only")
    parser.add_argument("--specs-only", action="store_true", help="Run specs database migrations only")
    parser.add_argument("--rollback", action="store_true", help="Rollback all migrations (CAREFUL!)")
    parser.add_argument("--check-status", action="store_true", help="Check current migration status")

    args = parser.parse_args()

    runner = MigrationRunner()

    # Validate configuration
    if not runner.validate_config():
        sys.exit(1)

    # Run appropriate migration
    try:
        if args.check_status:
            print("\nMigration Status:")
            auth_version = runner.get_current_version("socrates_auth", runner.auth_db_url)
            specs_version = runner.get_current_version("socrates_specs", runner.specs_db_url)
            print(f"  socrates_auth: {auth_version or 'not initialized'}")
            print(f"  socrates_specs: {specs_version or 'not initialized'}")
            success = True
        elif args.rollback:
            success = runner.rollback_all()
        elif args.auth_only:
            success = runner.run_auth_only()
        elif args.specs_only:
            success = runner.run_specs_only()
        else:
            success = runner.run_all_migrations()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
