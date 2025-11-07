#!/usr/bin/env python3
"""
Verify all dependencies are installed and compatible.
Run this before starting Phase 1 implementation.

Usage:
    python scripts/verify_dependencies.py
"""

import sys
import importlib.metadata as metadata  # Python 3.8+ (we require 3.12+)

REQUIRED_PACKAGES = {
    # Package name: (min_version, purpose)
    "fastapi": ("0.121.0", "Web framework"),
    "uvicorn": ("0.34.0", "ASGI server"),
    "sqlalchemy": ("2.0.44", "ORM"),
    "alembic": ("1.14.0", "Database migrations"),
    "pydantic": ("2.12.3", "Data validation"),
    "anthropic": ("0.40.0", "Claude API client"),
    "pytest": ("8.3.4", "Testing framework"),
    "psycopg2-binary": ("2.9.10", "PostgreSQL driver (sync)"),
    "asyncpg": ("0.30.0", "PostgreSQL driver (async)"),
    "PyJWT": ("2.10.1", "JWT tokens"),
    "passlib": ("1.7.4", "Password hashing"),
    "bcrypt": ("4.2.1", "Bcrypt algorithm"),
    "cryptography": ("44.0.0", "Cryptographic primitives"),
}

OPTIONAL_PACKAGES = {
    "black": ("24.10.0", "Code formatter (dev)"),
    "ruff": ("0.8.4", "Linter (dev)"),
    "mypy": ("1.13.0", "Type checker (dev)"),
}


def parse_version(version_str: str) -> tuple:
    """Parse version string into tuple for comparison."""
    return tuple(map(int, version_str.split(".")[:3]))


def check_package(name: str, min_version: str, purpose: str, optional: bool = False) -> bool:
    """Check if package is installed with correct version."""
    try:
        version = metadata.version(name)
        version_tuple = parse_version(version)
        min_version_tuple = parse_version(min_version)

        if version_tuple >= min_version_tuple:
            print("[OK] {}=={} ({})".format(name, version, purpose))
            return True
        else:
            marker = "[!]" if optional else "[X]"
            print("{} {}=={} - Need >={} ({})".format(marker, name, version, min_version, purpose))
            return optional  # Optional packages don't fail
    except Exception:
        marker = "[!]" if optional else "[X]"
        print("{} {} NOT INSTALLED ({})".format(marker, name, purpose))
        return optional  # Optional packages don't fail


def main():
    """Run all dependency checks."""
    print("[*] Checking Socrates2 Dependencies...\n")
    print("=" * 70)
    print("REQUIRED PACKAGES (Production)")
    print("=" * 70)

    all_ok = True
    for package, (min_version, purpose) in REQUIRED_PACKAGES.items():
        if not check_package(package, min_version, purpose, optional=False):
            all_ok = False

    print("\n" + "=" * 70)
    print("OPTIONAL PACKAGES (Development)")
    print("=" * 70)

    for package, (min_version, purpose) in OPTIONAL_PACKAGES.items():
        check_package(package, min_version, purpose, optional=True)

    print("\n" + "=" * 70)
    if all_ok:
        print("[OK] ALL REQUIRED DEPENDENCIES OK - Ready for Phase 1!")
        print("\nYou can now run:")
        print("  1. alembic upgrade head  # Create database tables")
        print("  2. pytest               # Run tests")
        print("  3. uvicorn app.main:app # Start server")
        sys.exit(0)
    else:
        print("[X] MISSING OR OUTDATED DEPENDENCIES")
        print("\n[*] To install all dependencies:")
        print("  pip install -r requirements.txt")
        print("\n[*] To install dev dependencies:")
        print("  pip install -r requirements-dev.txt")
        print("\n[*] See DEPENDENCIES_AND_CONFLICTS.md for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
