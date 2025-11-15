#!/usr/bin/env python3
import requests
import json
import time
import sys
from uuid import uuid4
from datetime import datetime

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

print("\n" + "="*80)
print("SYSTEMATIC PROBLEM MAPPING TEST")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backend URL: {BASE_URL}\n")

results = {}

# ============================================================================
# SETUP: Create test user and project
# ============================================================================
print("\n" + "-"*80)
print("SETUP: Creating test user...")
print("-"*80)

test_username = f"testmap_{uuid4().hex[:8]}"
test_email = f"map_{uuid4().hex[:8]}@test.com"
test_password = "TestPass123!"

try:
    reg_resp = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "name": "Test",
            "surname": "Map"
        },
        headers=HEADERS,
        timeout=10
    )

    if reg_resp.status_code in [200, 201]:
        user_data = reg_resp.json()
        user_id = user_data.get('user_id') or user_data.get('id')
        access_token = user_data.get('access_token')
        print(f"✓ User created: {user_id}")
        print(f"  Username: {test_username}")

        AUTH_HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    else:
        print(f"✗ Registration failed: {reg_resp.status_code}")
        print(f"  Response: {reg_resp.text}")
        exit(1)
except Exception as e:
    print(f"✗ Registration error: {e}")
    exit(1)

# Create project
print("\nSETUP: Creating test project...")
try:
    proj_resp = requests.post(
        f"{BASE_URL}/api/v1/projects",
        json={
            "name": "Test Project",
            "description": "Test project for problem mapping"
        },
        headers=AUTH_HEADERS,
        timeout=10
    )

    if proj_resp.status_code in [200, 201]:
        project_data = proj_resp.json()
        # ID can be at top level or nested in 'data'
        project_id = project_data.get('id') or project_data.get('project_id')
        if not project_id and 'data' in project_data:
            project_id = project_data['data'].get('id') or project_data['data'].get('project_id')
        print(f"✓ Project created: {project_id}")
    else:
        print(f"✗ Project creation failed: {proj_resp.status_code}")
        print(f"  Response: {proj_resp.text}")
        exit(1)
except Exception as e:
    print(f"✗ Project creation error: {e}")
    exit(1)

# Create socratic session
print("\nSETUP: Creating socratic session...")
try:
    sess_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/sessions",
        json={
            "mode": "socratic",
            "domain": "programming"
        },
        headers=AUTH_HEADERS,
        timeout=10
    )

    if sess_resp.status_code in [200, 201]:
        session_data = sess_resp.json()
        session_id = session_data.get('id')
        print(f"✓ Socratic session created: {session_id}")
    else:
        print(f"✗ Session creation failed: {sess_resp.status_code}")
        print(f"  Response: {sess_resp.text}")
        exit(1)
except Exception as e:
    print(f"✗ Session creation error: {e}")
    exit(1)

# ============================================================================
# TEST 1: Socratic Mode - Get Next Question
# ============================================================================
print("\n" + "-"*80)
print("TEST 1: Socratic Mode - Get Next Question")
print("-"*80)

try:
    t_start = time.time()
    q_resp = requests.get(
        f"{BASE_URL}/api/v1/sessions/{session_id}/next-question",
        headers=AUTH_HEADERS,
        timeout=60
    )
    elapsed = time.time() - t_start

    results['test1_socratic_question'] = {
        'status_code': q_resp.status_code,
        'elapsed': f"{elapsed:.2f}s",
        'success': q_resp.status_code == 200
    }

    if q_resp.status_code == 200:
        q_data = q_resp.json()
        question_text = q_data.get('question')
        if question_text:
            print(f"✓ PASS - Question generated in {elapsed:.2f}s")
            print(f"  Question: {question_text[:100]}...")
            results['test1_socratic_question']['error'] = None
        else:
            print(f"✗ FAIL - No question text in response")
            print(f"  Response: {q_data}")
            results['test1_socratic_question']['error'] = "No question text"
    else:
        print(f"✗ FAIL - Status {q_resp.status_code}")
        print(f"  Response: {q_resp.text[:200]}")
        results['test1_socratic_question']['error'] = q_resp.text[:100]

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test1_socratic_question'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# TEST 2: Switch to Direct Chat Mode
# ============================================================================
print("\n" + "-"*80)
print("TEST 2: Switch to Direct Chat Mode")
print("-"*80)

try:
    t_start = time.time()
    mode_resp = requests.put(
        f"{BASE_URL}/api/v1/sessions/{session_id}/mode",
        json={"mode": "direct_chat"},
        headers=AUTH_HEADERS,
        timeout=10
    )
    elapsed = time.time() - t_start

    results['test2_switch_mode'] = {
        'status_code': mode_resp.status_code,
        'elapsed': f"{elapsed:.2f}s",
        'success': mode_resp.status_code == 200
    }

    if mode_resp.status_code == 200:
        mode_data = mode_resp.json()
        new_mode = mode_data.get('mode')
        print(f"✓ PASS - Mode switched to {new_mode} in {elapsed:.2f}s")
        results['test2_switch_mode']['error'] = None
    else:
        print(f"✗ FAIL - Status {mode_resp.status_code}")
        print(f"  Response: {mode_resp.text[:200]}")
        results['test2_switch_mode']['error'] = mode_resp.text[:100]

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test2_switch_mode'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# TEST 3: Send Chat Message
# ============================================================================
print("\n" + "-"*80)
print("TEST 3: Send Chat Message in Direct Mode")
print("-"*80)

try:
    t_start = time.time()
    chat_resp = requests.post(
        f"{BASE_URL}/api/v1/sessions/{session_id}/chat",
        json={"message": "I want to build a REST API for managing user profiles"},
        headers=AUTH_HEADERS,
        timeout=60
    )
    elapsed = time.time() - t_start

    results['test3_chat_message'] = {
        'status_code': chat_resp.status_code,
        'elapsed': f"{elapsed:.2f}s",
        'success': chat_resp.status_code == 200
    }

    if chat_resp.status_code == 200:
        chat_data = chat_resp.json()
        response = chat_data.get('response')
        if response:
            print(f"✓ PASS - Chat response received in {elapsed:.2f}s")
            print(f"  Response: {response[:100]}...")
            results['test3_chat_message']['error'] = None
        else:
            print(f"✗ FAIL - No response text")
            print(f"  Response data: {chat_data}")
            results['test3_chat_message']['error'] = "No response"
    else:
        print(f"✗ FAIL - Status {chat_resp.status_code}")
        print(f"  Response: {chat_resp.text[:200]}")
        results['test3_chat_message']['error'] = chat_resp.text[:100]

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test3_chat_message'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# TEST 4: Submit Answer (switch back to socratic first)
# ============================================================================
print("\n" + "-"*80)
print("TEST 4: Submit Answer")
print("-"*80)

try:
    # First switch back to socratic mode
    switch_back = requests.put(
        f"{BASE_URL}/api/v1/sessions/{session_id}/mode",
        json={"mode": "socratic"},
        headers=AUTH_HEADERS,
        timeout=10
    )

    if switch_back.status_code == 200:
        print("  (Switched back to socratic mode)")

        t_start = time.time()
        answer_resp = requests.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/answer",
            json={"answer": "I need to build a REST API for user profiles with authentication and profile management"},
            headers=AUTH_HEADERS,
            timeout=60
        )
        elapsed = time.time() - t_start

        results['test4_submit_answer'] = {
            'status_code': answer_resp.status_code,
            'elapsed': f"{elapsed:.2f}s",
            'success': answer_resp.status_code == 200
        }

        if answer_resp.status_code == 200:
            ans_data = answer_resp.json()
            print(f"✓ PASS - Answer submitted in {elapsed:.2f}s")
            print(f"  Result: {ans_data.get('message', 'Success')}")
            results['test4_submit_answer']['error'] = None
        else:
            print(f"✗ FAIL - Status {answer_resp.status_code}")
            print(f"  Response: {answer_resp.text[:200]}")
            results['test4_submit_answer']['error'] = answer_resp.text[:100]
    else:
        print(f"✗ FAIL - Could not switch back to socratic mode")
        results['test4_submit_answer'] = {
            'status_code': 'SETUP_FAIL',
            'success': False,
            'error': 'Could not switch mode'
        }

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test4_submit_answer'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# TEST 5: Get Session History
# ============================================================================
print("\n" + "-"*80)
print("TEST 5: Get Session History")
print("-"*80)

try:
    t_start = time.time()
    hist_resp = requests.get(
        f"{BASE_URL}/api/v1/sessions/{session_id}/history",
        headers=AUTH_HEADERS,
        timeout=10
    )
    elapsed = time.time() - t_start

    results['test5_history'] = {
        'status_code': hist_resp.status_code,
        'elapsed': f"{elapsed:.2f}s",
        'success': hist_resp.status_code == 200
    }

    if hist_resp.status_code == 200:
        hist_data = hist_resp.json()
        messages = hist_data.get('messages', [])
        print(f"✓ PASS - History retrieved in {elapsed:.2f}s")
        print(f"  Messages: {len(messages)} entries")
        results['test5_history']['error'] = None
    else:
        print(f"✗ FAIL - Status {hist_resp.status_code}")
        print(f"  Response: {hist_resp.text[:200]}")
        results['test5_history']['error'] = hist_resp.text[:100]

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test5_history'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# TEST 6: Delete Project
# ============================================================================
print("\n" + "-"*80)
print("TEST 6: Delete Project")
print("-"*80)

try:
    t_start = time.time()
    del_resp = requests.delete(
        f"{BASE_URL}/api/v1/projects/{project_id}",
        headers=AUTH_HEADERS,
        timeout=10
    )
    elapsed = time.time() - t_start

    results['test6_delete_project'] = {
        'status_code': del_resp.status_code,
        'elapsed': f"{elapsed:.2f}s",
        'success': del_resp.status_code in [200, 204]
    }

    if del_resp.status_code in [200, 204]:
        print(f"✓ PASS - Project deleted in {elapsed:.2f}s")
        results['test6_delete_project']['error'] = None
    else:
        print(f"✗ FAIL - Status {del_resp.status_code}")
        print(f"  Response: {del_resp.text[:200]}")
        results['test6_delete_project']['error'] = del_resp.text[:100]

except Exception as e:
    print(f"✗ ERROR - {e}")
    results['test6_delete_project'] = {
        'status_code': 'EXCEPTION',
        'success': False,
        'error': str(e)
    }

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

passed = sum(1 for r in results.values() if r.get('success'))
failed = len(results) - passed

print(f"\nTotal Tests: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

print("\nDetailed Results:")
print("-"*80)

test_names = {
    'test1_socratic_question': 'Socratic Question Generation',
    'test2_switch_mode': 'Mode Switching',
    'test3_chat_message': 'Chat Message Send',
    'test4_submit_answer': 'Answer Submission',
    'test5_history': 'Session History',
    'test6_delete_project': 'Project Deletion'
}

for test_key, test_name in test_names.items():
    if test_key in results:
        r = results[test_key]
        status = "✓ PASS" if r['success'] else "✗ FAIL"
        code = r.get('status_code', '?')
        elapsed = r.get('elapsed', '?')
        error = r.get('error', 'None')

        print(f"\n{status} - {test_name}")
        print(f"  Status Code: {code}")
        print(f"  Time: {elapsed}")
        if error and error != 'None':
            print(f"  Error: {error}")

print("\n" + "="*80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")
