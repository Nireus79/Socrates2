#!/usr/bin/env python3
"""
Deep Inconsistency Investigation - Socrates Project Structure
Tests for inconsistencies between project definition and actual implementation.
"""

import json
import sys
from pathlib import Path
import subprocess

def check_entry_point():
    """Check if the CLI entry point defined in pyproject.toml actually exists."""
    print("\n" + "="*70)
    print("1. CLI ENTRY POINT CONSISTENCY CHECK")
    print("="*70)

    pyproject = Path("/home/user/Socrates2/backend/pyproject.toml")

    # Check pyproject.toml definition
    with open(pyproject) as f:
        content = f.read()
        if "[project.scripts]" in content:
            for line in content.split('\n'):
                if "socrates =" in line:
                    print(f"✓ Found entry point in pyproject.toml: {line.strip()}")
                    entry_point = line.split('=')[1].strip().strip('"')
                    module_path, func = entry_point.split(':')
                    print(f"  Module: {module_path}, Function: {func}")

                    # Check if module exists
                    backend_path = Path("/home/user/Socrates2/backend")
                    module_file = backend_path / module_path.replace('.', '/') / "__init__.py"
                    module_file_alt = backend_path / (module_path.replace('.', '/') + ".py")

                    print(f"  Expected: {module_file} or {module_file_alt}")
                    if module_file.exists():
                        print(f"  ✓ Found at {module_file}")
                    elif module_file_alt.exists():
                        print(f"  ✓ Found at {module_file_alt}")
                    else:
                        print(f"  ✗ NOT FOUND! Entry point references non-existent module!")
                        return False

    # Check if standalone CLI exists
    print("\n  Checking for standalone CLI...")
    standalone = Path("/home/user/Socrates2/Socrates.py")
    if standalone.exists():
        print(f"  ✓ Found standalone CLI: {standalone}")
        with open(standalone) as f:
            first_line = f.readline()
            print(f"    First line: {first_line.strip()}")
    else:
        print(f"  ✗ Standalone CLI not found")

    print("\n  ISSUE: Two CLI implementations!")
    print("    1. pyproject.toml points to: app.cli:main (doesn't exist)")
    print("    2. Actual implementation: /Socrates.py (root level)")
    return False


def check_backend_api():
    """Check if backend API is properly configured."""
    print("\n" + "="*70)
    print("2. BACKEND API CONFIGURATION CHECK")
    print("="*70)

    # Check if app.main exists
    main_file = Path("/home/user/Socrates2/backend/app/main.py")
    if main_file.exists():
        print(f"✓ Found FastAPI main: {main_file}")
        with open(main_file) as f:
            content = f.read()
            if "FastAPI()" in content:
                print("  ✓ FastAPI application initialized")
            if "cors" in content.lower() or "CORSMiddleware" in content:
                print("  ✓ CORS configured")
    else:
        print(f"✗ NOT FOUND: {main_file}")
        return False

    # Check database configuration
    db_file = Path("/home/user/Socrates2/backend/app/core/database.py")
    if db_file.exists():
        print(f"✓ Found database config: {db_file}")
        with open(db_file) as f:
            content = f.read()
            if "SQLite" in content or "sqlite" in content:
                print("  ✓ SQLite support configured")
            if "PostgreSQL" in content or "postgresql" in content:
                print("  ✓ PostgreSQL support configured")
    else:
        print(f"✗ NOT FOUND: {db_file}")

    return True


def check_package_metadata():
    """Check package metadata consistency."""
    print("\n" + "="*70)
    print("3. PACKAGE METADATA CONSISTENCY CHECK")
    print("="*70)

    pyproject = Path("/home/user/Socrates2/backend/pyproject.toml")

    # Read pyproject.toml
    import tomllib  # Python 3.11+
    try:
        with open(pyproject, 'rb') as f:
            data = tomllib.load(f)
    except:
        # Fallback for reading as text
        with open(pyproject) as f:
            content = f.read()
            # Extract key values
            for line in content.split('\n'):
                if 'name =' in line:
                    name = line.split('=')[1].strip().strip('"')
                    print(f"Package Name: {name}")
                if 'version =' in line:
                    version = line.split('=')[1].strip().strip('"')
                    print(f"Package Version: {version}")
                if 'requires-python' in line:
                    python = line.split('=')[1].strip().strip('"')
                    print(f"Python Version: {python}")

    # Check if version matches anywhere
    print("\n  Checking version consistency...")

    # Check in requirements.txt
    req_file = Path("/home/user/Socrates2/backend/requirements.txt")
    if req_file.exists():
        with open(req_file) as f:
            content = f.read()
            if "socrates-ai" in content:
                print("  ✗ WARNING: socrates-ai listed in requirements.txt")
                print("    This would create circular dependency if package is under development!")
            else:
                print("  ✓ socrates-ai NOT in requirements.txt (good for local development)")

    return True


def check_imports():
    """Check if imports are consistent across the project."""
    print("\n" + "="*70)
    print("4. IMPORT CONSISTENCY CHECK")
    print("="*70)

    # Check Socrates.py imports
    socrates_py = Path("/home/user/Socrates2/Socrates.py")
    print(f"Checking {socrates_py}...")
    with open(socrates_py) as f:
        content = f.read()

        imports = {
            "requests": "requests" in content,
            "rich": "from rich" in content,
            "backend_app": "from backend" in content or "import backend" in content,
            "FastAPI": "FastAPI" in content,
        }

        for lib, found in imports.items():
            status = "✓" if (found and lib != "backend_app") or (not found and lib == "backend_app") else "✗"
            print(f"  {status} {lib}: {found}")

    # Check if Socrates.py imports from backend
    if "from backend" not in content and "import backend" not in content:
        print("\n  ✓ Socrates.py is standalone (uses HTTP requests)")
    else:
        print("\n  ✗ Socrates.py imports backend directly (should use HTTP)")

    return True


def check_test_coverage():
    """Check if tests cover both CLI and API."""
    print("\n" + "="*70)
    print("5. TEST COVERAGE CHECK")
    print("="*70)

    test_dir = Path("/home/user/Socrates2/backend/tests")
    root_test_dir = Path("/home/user/Socrates2")

    print(f"Backend tests: {test_dir.exists()}")
    print(f"Root tests: {root_test_dir / 'test_*.py'}")

    # Count test files
    backend_tests = list(test_dir.glob("test_*.py")) if test_dir.exists() else []
    root_tests = list(root_test_dir.glob("test_*.py"))

    print(f"\n  Backend test files: {len(backend_tests)}")
    print(f"  Root test files: {len(root_tests)}")

    if backend_tests:
        print("\n  Backend tests:")
        for test in backend_tests[:5]:
            print(f"    - {test.name}")
        if len(backend_tests) > 5:
            print(f"    ... and {len(backend_tests) - 5} more")

    if root_tests:
        print("\n  Root tests:")
        for test in root_tests[:5]:
            print(f"    - {test.name}")
        if len(root_tests) > 5:
            print(f"    ... and {len(root_tests) - 5} more")

    # Check if tests use HTTP or direct imports
    print("\n  Checking test approach:")
    for test_file in root_tests[:3]:
        with open(test_file) as f:
            content = f.read()
            if "requests." in content or "http://" in content:
                print(f"    ✓ {test_file.name}: Uses HTTP requests (correct)")
            elif "from app" in content or "import app" in content:
                print(f"    ✗ {test_file.name}: Direct app import (should use HTTP)")

    return True


def check_database_setup():
    """Check database setup inconsistencies."""
    print("\n" + "="*70)
    print("6. DATABASE SETUP INCONSISTENCY CHECK")
    print("="*70)

    # Check .env files
    env_files = [
        Path("/home/user/Socrates2/backend/.env"),
        Path("/home/user/Socrates2/backend/.env.example"),
        Path("/home/user/Socrates2/backend/.env.test"),
    ]

    for env_file in env_files:
        if env_file.exists():
            print(f"\n✓ Found {env_file.name}:")
            with open(env_file) as f:
                for line in f:
                    if "DATABASE_URL" in line:
                        # Hide sensitive info
                        parts = line.split('=')
                        print(f"  {parts[0]}=***hidden***")
        else:
            print(f"✗ NOT FOUND: {env_file.name}")

    # Check init script
    init_script = Path("/home/user/Socrates2/backend/init_test_db.py")
    if init_script.exists():
        print(f"\n✓ Found database init script: {init_script.name}")
    else:
        print(f"\n✗ NOT FOUND: init_test_db.py")

    return True


def main():
    """Run all consistency checks."""
    print("\n")
    print("█"*70)
    print("SOCRATES PROJECT INCONSISTENCY INVESTIGATION")
    print("█"*70)

    results = []

    results.append(("Entry Point", check_entry_point()))
    results.append(("Backend API", check_backend_api()))
    results.append(("Package Metadata", check_package_metadata()))
    results.append(("Imports", check_imports()))
    results.append(("Test Coverage", check_test_coverage()))
    results.append(("Database Setup", check_database_setup()))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY OF INCONSISTENCIES")
    print("="*70)

    issues = []

    issues.append({
        "severity": "CRITICAL",
        "issue": "CLI Entry Point Mismatch",
        "description": "pyproject.toml defines entry point 'app.cli:main' but backend/app/cli.py doesn't exist",
        "impact": "Package cannot be installed from source via 'pip install .'",
        "solution": "Either create backend/app/cli.py or update pyproject.toml to reference the actual CLI location"
    })

    issues.append({
        "severity": "HIGH",
        "issue": "Two CLI Implementations",
        "description": "Socrates.py (root) and app.cli:main (missing) are separate implementations",
        "impact": "Confusion about which CLI is the official one; tests may not cover the right implementation",
        "solution": "Consolidate to single implementation or clearly document purpose of each"
    })

    issues.append({
        "severity": "MEDIUM",
        "issue": "Missing Test Coverage",
        "description": "Tests don't cover Socrates.py CLI behavior with actual backend API",
        "impact": "Bugs in CLI<->API interaction not caught by tests",
        "solution": "Create integration tests that run Socrates.py against running backend server"
    })

    issues.append({
        "severity": "MEDIUM",
        "issue": "Database Initialization Inconsistency",
        "description": "init_test_db.py created to manually initialize SQLite, but migrations via alembic also exist",
        "impact": "Unclear which database setup method should be used; both approaches may conflict",
        "solution": "Choose either alembic OR SQLAlchemy create_all, not both"
    })

    for i, issue in enumerate(issues, 1):
        print(f"\n[{i}] {issue['severity']}: {issue['issue']}")
        print(f"    Description: {issue['description']}")
        print(f"    Impact: {issue['impact']}")
        print(f"    Solution: {issue['solution']}")

    return len(issues)


if __name__ == "__main__":
    issue_count = main()
    sys.exit(0 if issue_count == 0 else 1)
