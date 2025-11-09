#!/usr/bin/env python
"""Script to reorganize migrations into auth/ and specs/ directories"""

import os
import shutil
from pathlib import Path

VERSIONS_DIR = Path("../backend/alembic/versions")

# Migrations for socrates_auth database
AUTH_MIGRATIONS = {
    "001_create_users_table.py",
    "002_create_refresh_tokens_table.py",
    "020_add_user_identity_fields.py",
}

# All other migrations go to specs
# (automatically determined)

def main():
    """Reorganize migrations"""
    print("Organizing migrations...")

    # Ensure directories exist
    auth_dir = VERSIONS_DIR / "auth"
    specs_dir = VERSIONS_DIR / "specs"

    auth_dir.mkdir(exist_ok=True)
    specs_dir.mkdir(exist_ok=True)

    # Create __init__.py files
    (auth_dir / "__init__.py").write_text('"""Alembic migrations for socrates_auth database."""\n')
    (specs_dir / "__init__.py").write_text('"""Alembic migrations for socrates_specs database."""\n')

    # Move migrations
    auth_count = 0
    specs_count = 0

    for file_path in sorted(VERSIONS_DIR.glob("*.py")):
        if file_path.name in ("__init__.py",):
            continue

        if file_path.name in AUTH_MIGRATIONS:
            dest = auth_dir / file_path.name
            shutil.copy2(file_path, dest)
            print(f"  → auth/: {file_path.name}")
            auth_count += 1
        else:
            dest = specs_dir / file_path.name
            shutil.copy2(file_path, dest)
            print(f"  → specs/: {file_path.name}")
            specs_count += 1

    print(f"\nMigrations organized:")
    print(f"  Auth migrations: {auth_count}")
    print(f"  Specs migrations: {specs_count}")
    print(f"\nNext steps:")
    print(f"  1. Verify files were copied correctly")
    print(f"  2. Delete old .py files from {VERSIONS_DIR}")
    print(f"  3. Update alembic.ini to use separate version_locations")

if __name__ == "__main__":
    main()
