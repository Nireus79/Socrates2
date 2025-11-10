#!/usr/bin/env python3
"""
End-to-end test for debugging login and refresh token issues.
Tests: registration, login, token refresh, project operations
"""

import sys
import json
import requests
import time
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console

console = Console()

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def log_test(name, status, details=""):
    """Pretty print test results"""
    symbol = "[PASS]" if status else "[FAIL]"
    print(f"{symbol} {name}" + (f" - {details}" if details else ""))

def test_flow():
    """Run the complete end-to-end flow"""
    print("\n=== SOCRATES E2E TEST ===\n")

    # Test 1: Check backend health
    print("1. Checking backend health...")
    try:
        r = requests.get(f"{API_V1}/admin/health", timeout=2)
        status = r.status_code == 200
        log_test("HEALTH", status, f"Status {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend not running: {e}")
        return

    # Create test user
    username = f"testuser_{int(time.time())}"
    password = "Test@Password123"
    email = f"test_{int(time.time())}@example.com"

    # Test 2: Register user
    print("\n2. Registering test user...")
    r = requests.post(f"{API_V1}/auth/register", json={
        "username": username,
        "password": password,
        "email": email,
        "name": "Test",
        "surname": "User"
    })
    register_ok = r.status_code in [201, 409]  # 409 = already exists
    log_test("REGISTER", register_ok, f"Status {r.status_code}")

    # Test 3: Login
    print("\n3. Testing login...")
    r = requests.post(f"{API_V1}/auth/login", data={
        "username": username,
        "password": password
    })
    login_ok = r.status_code == 200
    tokens = r.json() if login_ok else {}
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    log_test("LOGIN", login_ok, f"Status {r.status_code}")
    if not login_ok:
        print(f"Response: {r.text}")

    # Test 4: Get current user
    print("\n4. Getting current user info...")
    if access_token:
        r = requests.get(f"{API_V1}/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_ok = r.status_code == 200
        log_test("GET_USER", user_ok, f"Status {r.status_code}")
    else:
        log_test("GET_USER", False, "No access token")

    # Test 5: Refresh token
    print("\n5. Testing token refresh...")
    if refresh_token:
        r = requests.post(f"{API_V1}/auth/refresh", json={
            "refresh_token": refresh_token
        })
        refresh_ok = r.status_code == 200
        new_tokens = r.json() if refresh_ok else {}
        log_test("REFRESH", refresh_ok, f"Status {r.status_code}")

        # Update token for next requests
        if refresh_ok:
            access_token = new_tokens.get("access_token")
            if access_token:
                print("  New token received")
    else:
        log_test("REFRESH", False, "No refresh token")

    # Test 6: Create project
    print("\n6. Creating test project...")
    if access_token:
        r = requests.post(f"{API_V1}/projects", json={
            "name": f"Test Project {int(time.time())}",
            "description": "E2E test project",
            "phase": "planning"
        }, headers={"Authorization": f"Bearer {access_token}"})
        project_ok = r.status_code == 201
        project_id = r.json().get("id") if project_ok else None
        log_test("CREATE_PROJECT", project_ok, f"Status {r.status_code}")
    else:
        log_test("CREATE_PROJECT", False, "No access token")

    # Test 7: List projects
    print("\n7. Listing projects...")
    if access_token:
        r = requests.get(f"{API_V1}/projects", headers={
            "Authorization": f"Bearer {access_token}"
        })
        list_ok = r.status_code == 200
        projects = r.json() if list_ok else []
        log_test("LIST_PROJECTS", list_ok, f"Status {r.status_code}, Found {len(projects)} project(s)")
    else:
        log_test("LIST_PROJECTS", False, "No access token")

    # Test 8: Logout
    print("\n8. Testing logout...")
    if access_token:
        r = requests.post(f"{API_V1}/auth/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })
        logout_ok = r.status_code == 200
        log_test("LOGOUT", logout_ok, f"Status {r.status_code}")
    else:
        log_test("LOGOUT", False, "No access token")

    print("\n=== E2E Test Complete ===\n")

if __name__ == "__main__":
    test_flow()
