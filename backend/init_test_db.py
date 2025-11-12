#!/usr/bin/env python3
"""
Initialize in-memory SQLite databases for testing.
This script creates the necessary tables using SQLAlchemy's create_all.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine_auth, engine_specs, Base
from app.models import User, RefreshToken, Project, Session

def init_test_databases():
    """Create all tables in both test databases."""
    print("Initializing test databases...")

    # Create all tables in auth database
    print("Creating tables in auth database...")
    Base.metadata.create_all(bind=engine_auth)
    print("✓ Auth database tables created")

    # Create all tables in specs database
    print("Creating tables in specs database...")
    Base.metadata.create_all(bind=engine_specs)
    print("✓ Specs database tables created")

    print("\nTest databases initialized successfully!")

if __name__ == "__main__":
    init_test_databases()
