"""
Development environment setup script.
Run this to verify your Python environment is correctly configured.
"""
import sys
from pathlib import Path

def check_environment():
    """Check if development environment is correctly set up"""
    print("=" * 60)
    print("Socrates2 Development Environment Check")
    print("=" * 60)

    # Check Python version
    print(f"\n✓ Python version: {sys.version}")
    if sys.version_info < (3, 12):
        print("  ⚠️  WARNING: Python 3.12+ recommended")

    # Check current directory
    current_dir = Path.cwd()
    print(f"\n✓ Current directory: {current_dir}")

    # Check if we're in backend directory
    if current_dir.name != "backend":
        print("  ⚠️  WARNING: You should run this from the 'backend' directory")
        print(f"     cd {current_dir / 'backend'}")

    # Check if app directory exists
    app_dir = current_dir / "app"
    if app_dir.exists():
        print(f"\n✓ app/ directory found: {app_dir}")
    else:
        print(f"\n❌ app/ directory NOT found at: {app_dir}")
        print("   Make sure you're in the backend directory!")
        return False

    # Try importing app
    print("\n" + "=" * 60)
    print("Testing Imports")
    print("=" * 60)

    try:
        import app
        print("✓ Successfully imported 'app'")
        print(f"  Location: {app.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import 'app': {e}")
        print("\nTo fix this:")
        print("1. Make sure you're in the 'backend' directory")
        print("2. In PyCharm: Right-click 'backend' → Mark Directory as → Sources Root")
        return False

    # Try importing models
    try:
        from app.models.user import User
        print("✓ Successfully imported User model")
    except ImportError as e:
        print(f"❌ Failed to import User: {e}")
        return False

    # Try importing core
    try:
        from app.core.config import settings
        print("✓ Successfully imported settings")
    except ImportError as e:
        print(f"❌ Failed to import settings: {e}")
        return False

    # Check .env file
    env_file = current_dir / ".env"
    if env_file.exists():
        print(f"\n✓ .env file exists: {env_file}")
    else:
        print(f"\n⚠️  .env file NOT found at: {env_file}")
        print("   Copy .env.example to .env and configure it")

    # Check dependencies
    print("\n" + "=" * 60)
    print("Checking Dependencies")
    print("=" * 60)

    required_packages = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "psycopg2",
        "alembic",
        "passlib",
        "python-jose",
        "anthropic",
        "pytest"
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("\nInstall with:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements-dev.txt")
        return False

    # Summary
    print("\n" + "=" * 60)
    print("✅ Environment Check Complete - All Good!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  1. Tests: pytest tests/test_data_persistence.py -v")
    print("  2. Server: python -m uvicorn app.main:app --reload")
    print("  3. Docs: http://localhost:8000/docs")

    return True


if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
