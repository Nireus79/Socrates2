#!/usr/bin/env python3
"""
Direct registration test to diagnose the 500 error.
Tests the registration endpoint directly and shows exact error.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_registration():
    """Test registration endpoint directly."""
    print("\n" + "=" * 70)
    print("DIRECT REGISTRATION TEST")
    print("=" * 70)

    # Check server is running
    try:
        health = requests.get(f"{BASE_URL}/admin/health", timeout=2)
        print(f"\n✓ Server is running (health: {health.status_code})")
    except Exception as e:
        print(f"\n✗ Server not running: {e}")
        return False

    # Test registration data
    # Username must match pattern: ^[a-zA-Z0-9_-]+$ (no dots allowed!)
    import random
    test_user = {
        "username": f"testuser_{random.randint(10000, 99999)}",
        "name": "Test",
        "surname": "User",
        "email": f"test_{random.randint(10000, 99999)}@example.com",
        "password": "TestPassword123!"
    }

    print(f"\nAttempting registration with:")
    print(f"  username: {test_user['username']}")
    print(f"  name: {test_user['name']}")
    print(f"  surname: {test_user['surname']}")
    print(f"  email: {test_user['email']}")
    print(f"  password: {'*' * len(test_user['password'])}")

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            timeout=10
        )

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        try:
            response_json = response.json()
            print(f"\nResponse Body:")
            print(json.dumps(response_json, indent=2))
        except:
            print(f"\nResponse Body (raw):")
            print(response.text[:500])

        if response.status_code == 201:
            print("\n✓ Registration successful!")
            return True
        elif response.status_code == 500:
            print("\n✗ Server error (500) - See response above for details")
            return False
        else:
            print(f"\n✗ Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("\n✗ Request timeout - server may be hanging")
        return False
    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_required_fields():
    """Test with missing fields to check validation."""
    print("\n" + "=" * 70)
    print("FIELD VALIDATION TEST")
    print("=" * 70)

    import random
    test_cases = [
        {
            "name": "Missing username",
            "data": {"name": "Test", "surname": "User", "email": "test@example.com", "password": "Pass123!"}
        },
        {
            "name": "Missing email",
            "data": {"username": "testuser123", "name": "Test", "surname": "User", "password": "Pass123!"}
        },
        {
            "name": "Missing password",
            "data": {"username": "testuser456", "name": "Test", "surname": "User", "email": "test@example.com"}
        },
        {
            "name": "All fields (valid)",
            "data": {"username": f"test{random.randint(10000, 99999)}", "name": "Test", "surname": "User", "email": f"test{random.randint(10000, 99999)}@example.com", "password": "TestPass123!"}
        }
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=test_case['data'],
                timeout=5
            )
            print(f"  Status: {response.status_code}")
            if response.status_code >= 400:
                try:
                    error = response.json()
                    print(f"  Error: {error.get('detail', 'Unknown error')}")
                except:
                    print(f"  Error: {response.text[:100]}")
        except Exception as e:
            print(f"  Exception: {e}")


if __name__ == "__main__":
    print("\nSOCRATES REGISTRATION DIAGNOSTIC\n")

    # Test 1: Direct registration
    reg_ok = test_registration()

    # Test 2: Field validation
    test_required_fields()

    # Summary
    print("\n" + "=" * 70)
    if reg_ok:
        print("✓ Registration test passed!")
    else:
        print("✗ Registration test failed - check output above for error details")
    print("=" * 70)
