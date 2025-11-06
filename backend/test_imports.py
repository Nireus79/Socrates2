#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
Run this to verify the package structure is correct.

Usage:
    cd /path/to/Socrates2/backend
    python test_imports.py
"""
import sys
from pathlib import Path


def test_imports():
    """Test that all critical imports work"""
    print("=" * 70)
    print("Testing Import Paths - Socrates2 Backend")
    print("=" * 70)

    errors = []
    warnings = []

    # Test 1: Basic app import
    print("\n[1/12] Testing: import app")
    try:
        import app
        print(f"  ✓ Success - app package at: {Path(app.__file__).parent}")
    except ImportError as e:
        errors.append(f"Failed to import app: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 2: Core config
    print("\n[2/12] Testing: from app.core.config import settings")
    try:
        from app.core.config import settings
        print(f"  ✓ Success - settings loaded")
        print(f"     Environment: {settings.ENVIRONMENT}")
    except ImportError as e:
        errors.append(f"Failed to import settings: {e}")
        print(f"  ✗ FAILED: {e}")
    except Exception as e:
        warnings.append(f"Settings imported but error on access: {e}")
        print(f"  ⚠ Warning: Settings imported but error: {e}")

    # Test 3: Database
    print("\n[3/12] Testing: from app.core.database import get_db_auth, Base")
    try:
        from app.core.database import get_db_auth, get_db_specs, Base
        print(f"  ✓ Success - database functions imported")
    except ImportError as e:
        errors.append(f"Failed to import database: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 4: Security
    print("\n[4/12] Testing: from app.core.security import create_access_token")
    try:
        from app.core.security import create_access_token, get_current_user
        print(f"  ✓ Success - security functions imported")
    except ImportError as e:
        errors.append(f"Failed to import security: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 5: Dependencies
    print("\n[5/12] Testing: from app.core.dependencies import ServiceContainer")
    try:
        from app.core.dependencies import ServiceContainer, get_service_container
        print(f"  ✓ Success - ServiceContainer imported")
    except ImportError as e:
        errors.append(f"Failed to import ServiceContainer: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 6: BaseModel
    print("\n[6/12] Testing: from app.models.base import BaseModel")
    try:
        from app.models.base import BaseModel
        print(f"  ✓ Success - BaseModel imported")
    except ImportError as e:
        errors.append(f"Failed to import BaseModel: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 7: User model
    print("\n[7/12] Testing: from app.models.user import User")
    try:
        from app.models.user import User
        print(f"  ✓ Success - User model imported")
        # Test password hashing
        hashed = User.hash_password("test123")
        print(f"     Password hashing works: {hashed[:20]}...")
    except ImportError as e:
        errors.append(f"Failed to import User: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 8: BaseAgent
    print("\n[8/12] Testing: from app.agents.base import BaseAgent")
    try:
        from app.agents.base import BaseAgent
        print(f"  ✓ Success - BaseAgent imported")
    except ImportError as e:
        errors.append(f"Failed to import BaseAgent: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 9: Orchestrator
    print("\n[9/12] Testing: from app.agents.orchestrator import AgentOrchestrator")
    try:
        from app.agents.orchestrator import AgentOrchestrator, get_orchestrator
        print(f"  ✓ Success - AgentOrchestrator imported")
    except ImportError as e:
        errors.append(f"Failed to import AgentOrchestrator: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 10: Auth API
    print("\n[10/12] Testing: from app.api import auth")
    try:
        from app.api import auth
        print(f"  ✓ Success - auth API imported")
        print(f"     Router prefix: {auth.router.prefix}")
    except ImportError as e:
        errors.append(f"Failed to import auth API: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 11: Admin API
    print("\n[11/12] Testing: from app.api import admin")
    try:
        from app.api import admin
        print(f"  ✓ Success - admin API imported")
        print(f"     Router prefix: {admin.router.prefix}")
    except ImportError as e:
        errors.append(f"Failed to import admin API: {e}")
        print(f"  ✗ FAILED: {e}")

    # Test 12: Main app
    print("\n[12/12] Testing: from app.main import app")
    try:
        from app.main import app as fastapi_app
        print(f"  ✓ Success - FastAPI app imported")
        print(f"     App title: {fastapi_app.title}")
    except ImportError as e:
        errors.append(f"Failed to import main app: {e}")
        print(f"  ✗ FAILED: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if errors:
        print(f"\n❌ FAILED - {len(errors)} import error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("\n💡 To fix:")
        print("  1. Make sure you're in the 'backend' directory")
        print("  2. In PyCharm: Right-click 'backend' → Mark Directory as → Sources Root")
        print("  3. Check that all dependencies are installed:")
        print("     pip install -r requirements.txt")
        return False

    if warnings:
        print(f"\n⚠ {len(warnings)} warning(s):\n")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    print("\n✅ ALL IMPORTS SUCCESSFUL!")
    print("\nYour Python path is configured correctly.")
    print("\nNext steps:")
    print("  1. Run tests: pytest tests/test_data_persistence.py -v")
    print("  2. Start server: python -m uvicorn app.main:app --reload")
    print("  3. Open docs: http://localhost:8000/docs")

    return True


def check_directory():
    """Check if we're in the correct directory"""
    cwd = Path.cwd()

    if cwd.name != "backend":
        print("⚠ WARNING: You should run this from the 'backend' directory")
        print(f"Current directory: {cwd}")
        print(f"\nPlease run:")
        print(f"  cd {cwd / 'backend' if (cwd / 'backend').exists() else 'backend'}")
        print(f"  python test_imports.py")
        return False

    if not (cwd / "app").exists():
        print("❌ ERROR: 'app' directory not found!")
        print(f"Current directory: {cwd}")
        print("\nMake sure you're in the correct directory.")
        return False

    return True


if __name__ == "__main__":
    print(f"\nPython version: {sys.version}")
    print(f"Current directory: {Path.cwd()}\n")

    if not check_directory():
        sys.exit(1)

    success = test_imports()
    sys.exit(0 if success else 1)
