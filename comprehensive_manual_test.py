#!/usr/bin/env python3
"""
COMPREHENSIVE MANUAL TEST - Test EVERY endpoint and feature
Not a quick check - a thorough examination of ALL functionality
"""
import requests
import json
import time
import sys
from uuid import uuid4
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

all_results = []

def test(name, method, endpoint, data=None, expected_status=None):
    """Run a single test and record result"""
    try:
        url = f"{BASE_URL}{endpoint}"
        t_start = time.time()

        if method == "GET":
            resp = requests.get(url, headers=AUTH_HEADERS, timeout=60)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=AUTH_HEADERS, timeout=60)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=AUTH_HEADERS, timeout=60)
        elif method == "DELETE":
            resp = requests.delete(url, headers=AUTH_HEADERS, timeout=60)
        else:
            return None

        elapsed = time.time() - t_start

        success = expected_status is None or resp.status_code == expected_status
        status_str = "PASS" if success else "FAIL"

        result = {
            'test': name,
            'method': method,
            'endpoint': endpoint,
            'status_code': resp.status_code,
            'elapsed': f"{elapsed:.2f}s",
            'success': success,
            'response': resp.text[:200] if resp.text else ""
        }

        try:
            result['json'] = resp.json()
        except:
            pass

        all_results.append(result)

        print(f"\n[{status_str}] {name}")
        print(f"    Method: {method} {endpoint}")
        print(f"    Status: {resp.status_code} ({elapsed:.2f}s)")
        if not success and expected_status:
            print(f"    Expected: {expected_status}")
        if resp.text and len(resp.text) < 200:
            print(f"    Response: {resp.text[:150]}")

        return result

    except Exception as e:
        print(f"\n[ERROR] {name}")
        print(f"    {e}")
        all_results.append({
            'test': name,
            'method': method,
            'endpoint': endpoint,
            'status_code': 'EXCEPTION',
            'success': False,
            'error': str(e)
        })
        return None

print("\n" + "="*90)
print("COMPREHENSIVE MANUAL TEST - ALL ENDPOINTS AND FEATURES")
print("="*90)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# SETUP
# ============================================================================
print("\n" + "="*90)
print("SETUP: Creating test user, project, and sessions")
print("="*90)

test_username = f"comp_{uuid4().hex[:8]}"
test_email = f"c_{uuid4().hex[:8]}@test.com"

reg_resp = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": test_username,
        "email": test_email,
        "password": "TestPass123!",
        "name": "Comprehensive",
        "surname": "Test"
    },
    headers=HEADERS,
    timeout=10
)

if reg_resp.status_code not in [200, 201]:
    print(f"Registration failed: {reg_resp.text}")
    exit(1)

user_data = reg_resp.json()
user_id = user_data.get('user_id') or user_data.get('id')
access_token = user_data.get('access_token')

AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

print(f"User created: {user_id}")

# Create project
proj_resp = requests.post(
    f"{BASE_URL}/api/v1/projects",
    json={"name": "Comprehensive Test Project", "description": "Testing all features"},
    headers=AUTH_HEADERS,
    timeout=10
)

if proj_resp.status_code not in [200, 201]:
    print(f"Project creation failed: {proj_resp.text}")
    exit(1)

project_data = proj_resp.json()
project_id = project_data.get('id') or project_data.get('project_id')
if 'data' in project_data:
    project_id = project_data['data'].get('id') or project_data['data'].get('project_id')

print(f"Project created: {project_id}")

# Create socratic session
sess_resp = requests.post(
    f"{BASE_URL}/api/v1/projects/{project_id}/sessions",
    json={"mode": "socratic", "domain": "programming"},
    headers=AUTH_HEADERS,
    timeout=10
)

if sess_resp.status_code not in [200, 201]:
    print(f"Session creation failed: {sess_resp.text}")
    exit(1)

session_data = sess_resp.json()
socratic_session_id = session_data.get('id')
print(f"Socratic session created: {socratic_session_id}")

# Create direct chat session
chat_sess_resp = requests.post(
    f"{BASE_URL}/api/v1/projects/{project_id}/sessions",
    json={"mode": "direct_chat", "domain": "programming"},
    headers=AUTH_HEADERS,
    timeout=10
)

if chat_sess_resp.status_code not in [200, 201]:
    print(f"Chat session creation failed: {chat_sess_resp.text}")
    direct_chat_session_id = None
else:
    direct_chat_session_id = chat_sess_resp.json().get('id')
    print(f"Direct chat session created: {direct_chat_session_id}")

# ============================================================================
# TEST 1: PROJECT ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 1: PROJECT MANAGEMENT ENDPOINTS")
print("="*90)

test("1.1 - Get project details", "GET", f"/api/v1/projects/{project_id}", expected_status=200)
test("1.2 - List all projects", "GET", "/api/v1/projects", expected_status=200)
test("1.3 - Update project", "PUT", f"/api/v1/projects/{project_id}",
     {"name": "Updated Name", "description": "Updated desc"}, expected_status=200)
test("1.4 - Archive project", "PUT", f"/api/v1/projects/{project_id}/archive", {}, expected_status=200)
test("1.5 - Get project stats", "GET", f"/api/v1/projects/{project_id}/stats", expected_status=200)

# ============================================================================
# TEST 2: SESSION ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 2: SESSION MANAGEMENT ENDPOINTS")
print("="*90)

test("2.1 - Get session details", "GET", f"/api/v1/sessions/{socratic_session_id}", expected_status=200)
test("2.2 - List sessions", "GET", f"/api/v1/projects/{project_id}/sessions", expected_status=200)

# ============================================================================
# TEST 3: SOCRATIC MODE ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 3: SOCRATIC MODE ENDPOINTS")
print("="*90)

test("3.1 - Get next question", "GET", f"/api/v1/sessions/{socratic_session_id}/next-question",
     expected_status=200)
test("3.2 - Get next question (alternative)", "GET", f"/api/v1/sessions/{socratic_session_id}/question",
     expected_status=200)
test("3.3 - Submit answer", "POST", f"/api/v1/sessions/{socratic_session_id}/answer",
     {"answer": "This is a test answer"}, expected_status=200)
test("3.4 - Submit answer (alternative)", "POST", f"/api/v1/sessions/{socratic_session_id}/submit-answer",
     {"answer": "Test answer"}, expected_status=200)

# ============================================================================
# TEST 4: MODE SWITCHING ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 4: MODE SWITCHING ENDPOINTS")
print("="*90)

test("4.1 - Switch to direct_chat", "PUT", f"/api/v1/sessions/{socratic_session_id}/mode",
     {"mode": "direct_chat"}, expected_status=200)
test("4.2 - Switch mode (alternative endpoint)", "PUT", f"/api/v1/sessions/{socratic_session_id}/switch-mode",
     {"mode": "socratic"}, expected_status=200)
test("4.3 - Get current mode", "GET", f"/api/v1/sessions/{socratic_session_id}/mode",
     expected_status=200)

# ============================================================================
# TEST 5: DIRECT CHAT ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 5: DIRECT CHAT ENDPOINTS")
print("="*90)

test("5.1 - Send chat message", "POST", f"/api/v1/sessions/{direct_chat_session_id}/chat",
     {"message": "Tell me about building a REST API"}, expected_status=200)
test("5.2 - Send message (alternative)", "POST", f"/api/v1/sessions/{direct_chat_session_id}/message",
     {"message": "What are best practices?"}, expected_status=200)
test("5.3 - Send command - list specs", "POST", f"/api/v1/sessions/{direct_chat_session_id}/chat",
     {"message": "/list-specs"}, expected_status=200)
test("5.4 - Send command - export", "POST", f"/api/v1/sessions/{direct_chat_session_id}/chat",
     {"message": "/export json"}, expected_status=200)

# ============================================================================
# TEST 6: HISTORY AND CONTEXT ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 6: HISTORY AND CONTEXT ENDPOINTS")
print("="*90)

test("6.1 - Get session history", "GET", f"/api/v1/sessions/{socratic_session_id}/history",
     expected_status=200)
test("6.2 - Get conversation context", "GET", f"/api/v1/sessions/{socratic_session_id}/context",
     expected_status=200)
test("6.3 - Get recent messages", "GET", f"/api/v1/sessions/{socratic_session_id}/messages",
     expected_status=200)

# ============================================================================
# TEST 7: SPECIFICATION ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 7: SPECIFICATION ENDPOINTS")
print("="*90)

test("7.1 - List specifications", "GET", f"/api/v1/projects/{project_id}/specifications",
     expected_status=200)
test("7.2 - Get specs by category", "GET", f"/api/v1/projects/{project_id}/specifications/goals",
     expected_status=200)
test("7.3 - Create specification", "POST", f"/api/v1/projects/{project_id}/specifications",
     {"category": "goals", "content": "Test goal"}, expected_status=200)

# ============================================================================
# TEST 8: LLM ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 8: LLM AND PROVIDER ENDPOINTS")
print("="*90)

test("8.1 - List LLM providers", "GET", "/api/v1/llm/providers",
     expected_status=200)
test("8.2 - Get LLM usage stats", "GET", "/api/v1/llm/usage",
     expected_status=200)
test("8.3 - Set project LLM", "POST", f"/api/v1/projects/{project_id}/llm",
     {"provider": "anthropic", "model": "claude-opus"}, expected_status=200)
test("8.4 - Get project LLM config", "GET", f"/api/v1/projects/{project_id}/llm",
     expected_status=200)

# ============================================================================
# TEST 9: CONFLICT DETECTION ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 9: CONFLICT DETECTION ENDPOINTS")
print("="*90)

test("9.1 - List conflicts", "GET", f"/api/v1/projects/{project_id}/conflicts",
     expected_status=200)
test("9.2 - Detect conflicts", "POST", f"/api/v1/projects/{project_id}/conflicts/detect",
     {}, expected_status=200)
test("9.3 - Get conflict details", "GET", f"/api/v1/projects/{project_id}/conflicts/details",
     expected_status=200)

# ============================================================================
# TEST 10: EXPORT ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 10: EXPORT ENDPOINTS")
print("="*90)

test("10.1 - Export to JSON", "POST", f"/api/v1/projects/{project_id}/export",
     {"format": "json"}, expected_status=200)
test("10.2 - Export to Markdown", "POST", f"/api/v1/projects/{project_id}/export",
     {"format": "markdown"}, expected_status=200)
test("10.3 - Export to PDF", "POST", f"/api/v1/projects/{project_id}/export",
     {"format": "pdf"}, expected_status=200)

# ============================================================================
# TEST 11: QUALITY GATES ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 11: QUALITY GATES ENDPOINTS")
print("="*90)

test("11.1 - Get quality metrics", "GET", f"/api/v1/projects/{project_id}/quality",
     expected_status=200)
test("11.2 - Analyze question quality", "POST", "/api/v1/quality/analyze-question",
     {"question": "What are your goals?"}, expected_status=200)
test("11.3 - Check coverage", "GET", f"/api/v1/projects/{project_id}/coverage",
     expected_status=200)

# ============================================================================
# TEST 12: DELETION ENDPOINTS
# ============================================================================
print("\n" + "="*90)
print("TEST SUITE 12: DELETION ENDPOINTS")
print("="*90)

# Create a disposable session for deletion test
disp_sess = requests.post(
    f"{BASE_URL}/api/v1/projects/{project_id}/sessions",
    json={"mode": "direct_chat", "domain": "programming"},
    headers=AUTH_HEADERS,
    timeout=10
)
if disp_sess.status_code in [200, 201]:
    disp_session_id = disp_sess.json().get('id')
    test("12.1 - Delete session", "DELETE", f"/api/v1/sessions/{disp_session_id}",
         expected_status=200)

test("12.2 - Delete project", "DELETE", f"/api/v1/projects/{project_id}",
     expected_status=200)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*90)
print("TEST SUMMARY")
print("="*90)

passed = sum(1 for r in all_results if r.get('success'))
failed = len(all_results) - passed

print(f"\nTotal Tests: {len(all_results)}")
print(f"Passed: {passed} ({100*passed//len(all_results)}%)")
print(f"Failed: {failed} ({100*failed//len(all_results)}%)")

print("\n" + "-"*90)
print("FAILED TESTS (What needs fixing):")
print("-"*90)

for r in all_results:
    if not r.get('success'):
        print(f"\n[FAIL] {r['test']}")
        print(f"  {r['method']} {r['endpoint']}")
        print(f"  Status: {r.get('status_code', 'N/A')}")
        if 'error' in r:
            print(f"  Error: {r['error']}")
        if r.get('response'):
            print(f"  Response: {r['response'][:100]}")

print("\n" + "="*90)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*90)
