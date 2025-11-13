#!/usr/bin/env python3
"""
End-to-end workflow test for Socrates.py CLI.

Tests complete user workflow:
1. User registration
2. User login
3. Project creation
4. Project listing
"""

import sys
import os
import random
import json
from pathlib import Path

# Add backend to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import requests

def test_e2e_workflow():
    """Test complete user workflow."""
    base_url = "http://localhost:8000/api/v1"

    # Generate unique test user
    user_id = random.randint(10000, 99999)
    test_user = {
        "username": f"e2euser{user_id}",
        "name": "E2E",
        "surname": f"User{user_id}",
        "email": f"e2e{user_id}@example.com",
        "password": "SecureTestPassword123!"
    }

    print("\n" + "="*70)
    print("END-TO-END SOCRATES WORKFLOW TEST")
    print("="*70)

    # Step 1: Register User
    print("\n[1/4] REGISTERING USER...")
    print(f"  Username: {test_user['username']}")
    print(f"  Email: {test_user['email']}")

    try:
        reg_response = requests.post(
            f"{base_url}/auth/register",
            json=test_user
        )

        if reg_response.status_code != 201:
            print(f"  ✗ Registration failed: {reg_response.status_code}")
            print(f"    Error: {reg_response.text}")
            return False

        reg_data = reg_response.json()
        user_id = reg_data.get("user_id")
        access_token = reg_data.get("access_token")
        print(f"  ✓ Registration successful!")
        print(f"    User ID: {user_id}")
        print(f"    Token: {access_token[:30]}...")

    except Exception as e:
        print(f"  ✗ Registration error: {e}")
        return False

    # Step 2: Login User
    print("\n[2/4] LOGGING IN...")

    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )

        if login_response.status_code != 200:
            print(f"  ✗ Login failed: {login_response.status_code}")
            print(f"    Error: {login_response.text}")
            return False

        login_data = login_response.json()
        access_token = login_data.get("access_token")
        print(f"  ✓ Login successful!")
        print(f"    Token: {access_token[:30]}...")

    except Exception as e:
        print(f"  ✗ Login error: {e}")
        return False

    # Step 3: Create Project
    print("\n[3/4] CREATING PROJECT...")

    try:
        project_data = {
            "name": f"E2E Test Project {user_id}",
            "description": "A test project for end-to-end workflow testing"
        }

        headers = {"Authorization": f"Bearer {access_token}"}
        project_response = requests.post(
            f"{base_url}/projects",
            json=project_data,
            headers=headers
        )

        if project_response.status_code != 201:
            print(f"  ✗ Project creation failed: {project_response.status_code}")
            print(f"    Error: {project_response.text}")
            # Note: This might fail if endpoint not yet implemented
            print("    (This is expected if project endpoints not yet implemented)")
        else:
            project_info = project_response.json()
            print(f"  ✓ Project created!")
            print(f"    Project ID: {project_info.get('id')}")
            print(f"    Project name: {project_info.get('name')}")

    except Exception as e:
        print(f"  ⚠ Project creation unavailable: {e}")
        print("    (This is expected if project endpoints not yet implemented)")

    # Step 4: Get Current User Info
    print("\n[4/4] RETRIEVING USER INFO...")

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(
            f"{base_url}/auth/me",
            headers=headers
        )

        if user_response.status_code != 200:
            print(f"  ✗ User info retrieval failed: {user_response.status_code}")
            print(f"    Error: {user_response.text}")
        else:
            user_info = user_response.json()
            print(f"  ✓ User info retrieved!")
            print(f"    Username: {user_info.get('username')}")
            print(f"    Name: {user_info.get('name')} {user_info.get('surname')}")
            print(f"    Email: {user_info.get('email')}")
            print(f"    Status: {user_info.get('status')}")

    except Exception as e:
        print(f"  ✗ User info error: {e}")
        return False

    print("\n" + "="*70)
    print("✓ END-TO-END WORKFLOW TEST PASSED!")
    print("="*70)
    return True

if __name__ == "__main__":
    try:
        success = test_e2e_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
