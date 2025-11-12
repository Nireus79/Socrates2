#!/usr/bin/env python3
"""
Simple test to debug refresh token issue

⚠️ This test requires a running backend server on localhost:8000
It will be skipped if the server is not available.
"""

import requests
import json
import time
import pytest
import socket

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def is_server_available():
    """Check if server is running on localhost:8000"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False

@pytest.mark.integration
@pytest.mark.skipif(not is_server_available(), reason="Server not running on localhost:8000")
def test_flow():
    print("\n=== Testing Token Refresh ===\n")

    # Create test user
    username = f"testuser_{int(time.time())}"
    password = "Test@Password123"
    email = f"test_{int(time.time())}@example.com"

    print(f"1. Registering user: {username}")
    r = requests.post(f"{API_V1}/auth/register", json={
        "username": username,
        "password": password,
        "email": email,
        "name": "Test",
        "surname": "User"
    })
    print(f"   Status: {r.status_code}\n")

    print(f"2. Logging in...")
    r = requests.post(f"{API_V1}/auth/login", data={
        "username": username,
        "password": password
    })
    print(f"   Status: {r.status_code}")
    data = r.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    print(f"   Access Token: {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...\n")

    print(f"3. Testing token refresh...")
    r = requests.post(f"{API_V1}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    print(f"   Status: {r.status_code}")
    if r.status_code != 200:
        print(f"   ERROR RESPONSE:")
        print(json.dumps(r.json(), indent=2))
    else:
        print(f"   New tokens received")

    return True

if __name__ == "__main__":
    success = test_flow()
