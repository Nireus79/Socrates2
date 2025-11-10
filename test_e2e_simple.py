#!/usr/bin/env python3
"""
Simple end-to-end test of the Socrates CLI functionality.
"""

import sys
import json
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from Socrates import SocratesAPI

def test_flow():
    """Run the complete end-to-end flow"""
    api = SocratesAPI("http://localhost:8000", None)

    print("\n=== E2E Test Flow ===\n")

    # 1. Login
    print("1. Testing login...")
    try:
        login_result = api.login("Themis", "test1234")
        if login_result.get("success"):
            token = login_result.get("access_token")
            api.set_token(token)
            print("   [OK] Login successful")
        else:
            print(f"   [FAILED] Login failed: {login_result}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

    # 2. Get projects
    print("\n2. Getting projects...")
    try:
        projects = api.list_projects()
        if projects.get("success"):
            proj_list = projects.get("projects", [])
            print(f"   [OK] Found {len(proj_list)} projects")

            if proj_list:
                project_id = proj_list[0]["id"]
                project_name = proj_list[0].get("name", "Unknown")
                print(f"   Using project: {project_name} ({project_id})")
            else:
                print("   [FAILED] No projects found")
                return False
        else:
            print(f"   [FAILED] {projects}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

    # 3. Start a new session
    print("\n3. Starting new session...")
    try:
        session_result = api.start_session(project_id)
        if session_result.get("success"):
            session_id = session_result.get("session_id")
            session_data = session_result.get("session", {})
            print(f"   [OK] Session started: {session_id}")
            print(f"       Mode: {session_data.get('mode', 'unknown')}")
            print(f"       Status: {session_data.get('status', 'unknown')}")
        else:
            print(f"   [FAILED] {session_result}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. List sessions for the project
    print("\n4. Listing sessions for project...")
    try:
        sessions = api.list_sessions(project_id)
        if sessions.get("success"):
            sess_list = sessions.get("sessions", [])
            print(f"   [OK] Found {len(sess_list)} sessions")
            for i, s in enumerate(sess_list, 1):
                print(f"       {i}. {s.get('id', 'unknown')} - {s.get('status')} ({s.get('mode')})")
        else:
            print(f"   [FAILED] {sessions}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 5. Get next question
    print("\n5. Getting next question...")
    try:
        question_result = api.get_next_question(session_id)
        if question_result.get("success"):
            question = question_result.get("question")
            if isinstance(question, dict):
                q_text = question.get("text") or question.get("question", "No text")
            else:
                q_text = question or "No question"
            print(f"   [OK] Question received")
            print(f"       {q_text[:100]}...")
        else:
            print(f"   [FAILED] {question_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 6. Get session mode
    print("\n6. Getting session mode...")
    try:
        mode_result = api.get_session_mode(session_id)
        if mode_result.get("success"):
            mode = mode_result.get("mode", "unknown")
            print(f"   [OK] Current mode: {mode}")
        else:
            print(f"   [FAILED] {mode_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 7. Toggle mode
    print("\n7. Toggling to direct_chat mode...")
    try:
        toggle_result = api.set_session_mode(session_id, "direct_chat")
        if toggle_result.get("success"):
            new_mode = toggle_result.get("mode", "unknown")
            print(f"   [OK] Mode changed to: {new_mode}")
        else:
            print(f"   [FAILED] {toggle_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 8. Send chat message
    print("\n8. Sending chat message...")
    try:
        chat_result = api.send_chat_message(session_id, "Hello, I'm testing the chat mode")
        if chat_result.get("success"):
            print("[OK] Message sent successfully")
            if "response" in chat_result:
                response = chat_result['response']
                if isinstance(response, str):
                    print(f"   Response: {response[:100]}...")
                else:
                    print(f"   Response: {str(response)[:100]}...")
        else:
            print(f"   [FAILED] {chat_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 9. Pause session
    print("\n9. Pausing session...")
    try:
        pause_result = api.pause_session(session_id)
        if pause_result.get("success"):
            print(f"   [OK] Session paused")
        else:
            print(f"   [FAILED] {pause_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 10. Resume session
    print("\n10. Resuming session...")
    try:
        resume_result = api.resume_session(session_id)
        if resume_result.get("success"):
            print(f"   [OK] Session resumed")
        else:
            print(f"   [FAILED] {resume_result}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    print("\n=== E2E Test Complete ===\n")
    return True

if __name__ == "__main__":
    success = test_flow()
    sys.exit(0 if success else 1)
