#!/usr/bin/env python3
"""
Debug script to test list_projects API endpoint directly using cached token.
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Load cached token from config
config_file = Path.home() / ".socrates" / "config.json"
print(f"1. Loading token from {config_file}")

if not config_file.exists():
    print(f"   ERROR: Config file not found at {config_file}")
    exit(1)

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    token = config.get("access_token")
    if not token:
        print("   ERROR: No access_token in config")
        exit(1)
    print(f"   Token loaded: {token[:40]}...")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Now call list_projects
print("\n2. Calling list_projects...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

list_response = requests.get(
    f"{BASE_URL}/api/v1/projects?skip=0&limit=100",
    headers=headers
)

print(f"   Status: {list_response.status_code}")
try:
    list_data = list_response.json()
    print(f"   Response: {json.dumps(list_data, indent=2)}")
except Exception as e:
    print(f"   ERROR: {e}")
    print(f"   Raw response: {list_response.text}")
