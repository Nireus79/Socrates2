#!/usr/bin/env python3
"""
End-to-end test of the Socrates CLI functionality.
Tests: project creation, session start, mode switching, question retrieval
"""

import sys
import json
import requests
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from Socrates import SocratesAPI
from rich.console import Console

console = Console()

def test_flow():
    """Run the complete end-to-end flow"""
    api = SocratesAPI("http://localhost:8000", console)

    console.print("\n[bold cyan]=== E2E Test Flow ===[/bold cyan]\n")

    # 1. Login
    console.print("[yellow]1. Testing login...[/yellow]")
    try:
        login_result = api.login("Themis", "test1234")
        if login_result.get("success"):
            token = login_result.get("access_token")
            api.set_token(token)
            console.print("[green]✓ Login successful[/green]")
        else:
            console.print(f"[red]✗ Login failed: {login_result}[/red]")
            return
    except Exception as e:
        console.print(f"[red]✗ Login error: {e}[/red]")
        return

    # 2. Get projects
    console.print("\n[yellow]2. Getting projects...[/yellow]")
    try:
        projects = api.list_projects()
        if projects.get("success"):
            proj_list = projects.get("projects", [])
            console.print(f"[green]✓ Found {len(proj_list)} projects[/green]")

            if proj_list:
                project_id = proj_list[0]["id"]
                project_name = proj_list[0].get("name", "Unknown")
                console.print(f"  Using project: {project_name} ({project_id})")
            else:
                console.print("[red]✗ No projects found[/red]")
                return
        else:
            console.print(f"[red]✗ Failed to get projects: {projects}[/red]")
            return
    except Exception as e:
        console.print(f"[red]✗ Error getting projects: {e}[/red]")
        return

    # 3. Start a new session
    console.print("\n[yellow]3. Starting new session...[/yellow]")
    try:
        session_result = api.start_session(project_id)
        if session_result.get("success"):
            session_id = session_result.get("session_id")
            session_data = session_result.get("session", {})
            console.print(f"[green]✓ Session started: {session_id}[/green]")
            console.print(f"  Mode: {session_data.get('mode', 'unknown')}")
            console.print(f"  Status: {session_data.get('status', 'unknown')}")
        else:
            console.print(f"[red]✗ Failed to start session: {session_result}[/red]")
            return
    except Exception as e:
        console.print(f"[red]✗ Error starting session: {e}[/red]")
        return

    # 4. List sessions for the project
    console.print("\n[yellow]4. Listing sessions for project...[/yellow]")
    try:
        sessions = api.list_sessions(project_id)
        if sessions.get("success"):
            sess_list = sessions.get("sessions", [])
            console.print(f"[green]✓ Found {len(sess_list)} sessions[/green]")
            for i, s in enumerate(sess_list, 1):
                console.print(f"  {i}. {s.get('id', 'unknown')} - {s.get('status', 'unknown')} ({s.get('mode', 'unknown')})")
        else:
            console.print(f"[red]✗ Failed to list sessions: {sessions}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error listing sessions: {e}[/red]")

    # 5. Get next question
    console.print("\n[yellow]5. Getting next question...[/yellow]")
    try:
        question_result = api.get_next_question(session_id)
        if question_result.get("success"):
            question = question_result.get("question")
            if isinstance(question, dict):
                q_text = question.get("text") or question.get("question", "No text")
            else:
                q_text = question or "No question"
            console.print(f"[green]✓ Question received[/green]")
            console.print(f"  {q_text}")
        else:
            console.print(f"[red]✗ Failed to get question: {question_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error getting question: {e}[/red]")

    # 6. Get session mode
    console.print("\n[yellow]6. Getting session mode...[/yellow]")
    try:
        mode_result = api.get_session_mode(session_id)
        if mode_result.get("success"):
            mode = mode_result.get("mode", "unknown")
            console.print(f"[green]✓ Current mode: {mode}[/green]")
        else:
            console.print(f"[red]✗ Failed to get mode: {mode_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error getting mode: {e}[/red]")

    # 7. Toggle mode
    console.print("\n[yellow]7. Toggling to direct_chat mode...[/yellow]")
    try:
        toggle_result = api.set_session_mode(session_id, "direct_chat")
        if toggle_result.get("success"):
            new_mode = toggle_result.get("mode", "unknown")
            console.print(f"[green]✓ Mode changed to: {new_mode}[/green]")
        else:
            console.print(f"[red]✗ Failed to toggle mode: {toggle_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error toggling mode: {e}[/red]")

    # 8. Send chat message
    console.print("\n[yellow]8. Sending chat message...[/yellow]")
    try:
        chat_result = api.send_chat_message(session_id, "Hello, I'm testing the chat mode")
        if chat_result.get("success"):
            console.print("[green]✓ Message sent successfully[/green]")
            if "response" in chat_result:
                console.print(f"  Response: {chat_result['response'][:100]}...")
        else:
            console.print(f"[red]✗ Failed to send message: {chat_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error sending message: {e}[/red]")

    # 9. Pause session
    console.print("\n[yellow]9. Pausing session...[/yellow]")
    try:
        pause_result = api.pause_session(session_id)
        if pause_result.get("success"):
            console.print(f"[green]✓ Session paused[/green]")
        else:
            console.print(f"[red]✗ Failed to pause session: {pause_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error pausing session: {e}[/red]")

    # 10. Resume session
    console.print("\n[yellow]10. Resuming session...[/yellow]")
    try:
        resume_result = api.resume_session(session_id)
        if resume_result.get("success"):
            console.print(f"[green]✓ Session resumed[/green]")
        else:
            console.print(f"[red]✗ Failed to resume session: {resume_result}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error resuming session: {e}[/red]")

    console.print("\n[bold green]=== E2E Test Complete ===[/bold green]\n")

if __name__ == "__main__":
    test_flow()
