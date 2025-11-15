#!/usr/bin/env python
"""Run database migration for specs database."""
import os
import subprocess
import sys

os.chdir("backend")

# Set the database URL for specs
os.environ["DATABASE_URL_SPECS"] = "postgresql://postgres@localhost:5432/socrates_specs"
os.environ["DATABASE_URL"] = "postgresql://postgres@localhost:5432/socrates_specs"

# Run alembic upgrade for specs database (branch: specs@head)
result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "specs@head"], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

sys.exit(result.returncode)
