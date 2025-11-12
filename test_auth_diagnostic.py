#!/usr/bin/env python3
"""
Diagnostic script to test password hashing and login flow.
Helps debug why login fails after successful registration.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL_AUTH"] = "sqlite:///:memory:"
os.environ["DATABASE_URL_SPECS"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"

def test_password_hashing():
    """Test that password hashing works correctly."""
    from app.models import User

    print("=" * 60)
    print("Testing Password Hashing")
    print("=" * 60)

    # Test password
    test_password = "TestPassword123!"

    # Hash the password
    hashed = User.hash_password(test_password)
    print(f"\nOriginal password: {test_password}")
    print(f"Hashed password: {hashed[:20]}...{hashed[-20:]}")

    # Create a fake user object to test verify_password
    class FakeUser:
        def __init__(self, hashed_password):
            self.hashed_password = hashed_password

        def verify_password(self, password):
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(password, self.hashed_password)

    fake_user = FakeUser(hashed)

    # Test correct password
    is_valid = fake_user.verify_password(test_password)
    print(f"\nVerify with correct password: {is_valid}")

    if not is_valid:
        print("[ERROR] Password verification FAILED!")
        return False

    # Test wrong password
    is_valid_wrong = fake_user.verify_password("WrongPassword123!")
    print(f"Verify with wrong password: {is_valid_wrong}")

    if is_valid_wrong:
        print("[ERROR] Wrong password should NOT verify!")
        return False

    print("\n[OK] Password hashing works correctly!")
    return True


def test_database_registration_and_login():
    """Test registration and login with real database."""
    import requests
    import json

    print("\n" + "=" * 60)
    print("Testing Registration and Login Flow")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1"

    # Check if server is running
    try:
        response = requests.get(f"{base_url}/admin/health", timeout=2)
        print("\n[OK] Backend server is running")
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Backend server is NOT running at http://localhost:8000")
        print("Please start the server first:")
        print("  cd backend && python -m uvicorn app.main:app --reload")
        return False

    # Test user data
    test_user = {
        "username": f"debug_user_{os.getpid()}",
        "email": f"debug{os.getpid()}@test.com",
        "password": "TestPassword123!",
        "name": "Debug",
        "surname": "User"
    }

    print(f"\nTest user: {test_user['username']}")

    # Register
    print("\n1. Attempting registration...")
    try:
        reg_response = requests.post(
            f"{base_url}/auth/register",
            json=test_user
        )
        print(f"   Status: {reg_response.status_code}")

        if reg_response.status_code != 201:
            print(f"   Error: {reg_response.text}")
            return False

        reg_data = reg_response.json()
        print(f"   ✓ User registered: {reg_data.get('username')}")
        print(f"   User ID: {reg_data.get('user_id')}")

    except Exception as e:
        print(f"   [ERROR] Registration failed: {e}")
        return False

    # Try to login
    print("\n2. Attempting login...")
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        print(f"   Status: {login_response.status_code}")

        if login_response.status_code != 200:
            print(f"   Error: {login_response.text}")

            # Try with email instead of username
            print("\n   Trying login with email instead of username...")
            login_response = requests.post(
                f"{base_url}/auth/login",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"]
                }
            )
            print(f"   Status: {login_response.status_code}")
            if login_response.status_code != 200:
                print(f"   Error: {login_response.text}")
                return False

        login_data = login_response.json()
        print(f"   ✓ Login successful!")
        print(f"   Access token: {login_data.get('access_token')[:20]}...")

    except Exception as e:
        print(f"   [ERROR] Login failed: {e}")
        return False

    print("\n[OK] Registration and login flow works correctly!")
    return True


if __name__ == "__main__":
    print("\nSOCRATES PASSWORD HASHING DIAGNOSTIC\n")

    # Test 1: Password hashing
    hash_ok = test_password_hashing()

    # Test 2: Database registration and login
    flow_ok = test_database_registration_and_login()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Password hashing: {'✓ OK' if hash_ok else '✗ FAILED'}")
    print(f"Registration/Login flow: {'✓ OK' if flow_ok else '✗ FAILED'}")

    if hash_ok and flow_ok:
        print("\n[OK] All diagnostics passed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some diagnostics failed - see above for details")
        sys.exit(1)
