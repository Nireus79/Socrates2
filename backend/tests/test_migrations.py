#!/usr/bin/env python
"""Test migrations one by one to find the problem."""
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

# Get DB URL from environment
db_url = os.getenv('DATABASE_URL_AUTH')
if not db_url:
    print("ERROR: DATABASE_URL_AUTH not set")
    sys.exit(1)

os.environ['DATABASE_URL'] = db_url

def run_alembic(target_version):
    """Run alembic upgrade to target version."""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', target_version],
        capture_output=True,
        text=True,
        cwd='.'
    )
    return result

def check_current_version():
    """Check current migration version."""
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        engine.dispose()

print("Starting migration test...\n")
print(f"Current version: {check_current_version()}")

# Test migrations one by one
migration_sequence = ['008', '009', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021']

for version in migration_sequence:
    print(f"\nTesting upgrade to {version}...")
    result = run_alembic(version)

    if result.returncode == 0:
        current = check_current_version()
        print(f"  [OK] Successfully upgraded to {version} (current: {current})")
    else:
        print(f"  [FAIL] Failed to upgrade to {version}")
        print(f"  Return code: {result.returncode}")

        if result.stdout:
            print(f"\n  STDOUT:")
            for line in result.stdout.split('\n')[-20:]:
                if line.strip():
                    print(f"    {line}")

        if result.stderr:
            print(f"\n  STDERR:")
            for line in result.stderr.split('\n')[-20:]:
                if line.strip():
                    print(f"    {line}")

        print(f"\n  Stopping test at version {version}")
        break

print(f"\nFinal version: {check_current_version()}")
