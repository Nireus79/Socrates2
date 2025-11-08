#!/usr/bin/env python
"""Run Alembic migrations for both databases."""
import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migrations(db_name: str, db_url: str) -> bool:
    """Run Alembic migrations for a specific database."""
    print(f"\n{'='*60}")
    print(f"Running migrations for {db_name}")
    print(f"{'='*60}")

    # Set environment variable
    os.environ['DATABASE_URL'] = db_url

    # Run migrations with proper output capture
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )

    # Always print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print(f"\n[ERROR] Migration failed with return code {result.returncode}")
        return False

    return True

if __name__ == '__main__':
    db_url_auth = os.getenv('DATABASE_URL_AUTH')
    db_url_specs = os.getenv('DATABASE_URL_SPECS')

    if not db_url_auth:
        print("ERROR: DATABASE_URL_AUTH not set")
        sys.exit(1)
    if not db_url_specs:
        print("ERROR: DATABASE_URL_SPECS not set")
        sys.exit(1)

    # Run migrations for auth database first
    success_auth = run_migrations('socrates_auth', db_url_auth)
    if not success_auth:
        print(f"\nERROR: Migration failed for socrates_auth")
        sys.exit(1)

    # Run migrations for specs database
    success_specs = run_migrations('socrates_specs', db_url_specs)
    if not success_specs:
        print(f"\nERROR: Migration failed for socrates_specs")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("All migrations completed successfully!")
    print(f"{'='*60}")
