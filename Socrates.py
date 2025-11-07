#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Socrates2 - Interactive Development Shell

Automatically:
1. Starts the FastAPI server in the background
2. Keeps an interactive shell for testing and management
3. Provides commands to interact with the API

Usage:
    python Socrates.py        # Start with server running in background
"""

import subprocess
import sys
import os
import time
import requests
import json
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Ensure backend is in path
sys.path.insert(0, str(BACKEND_DIR))

API_URL = "http://localhost:8000"


class SocratesApp:
    """Socrates2 Development Shell with Background Server"""

    def __init__(self):
        self.running = True
        self.server_process = None
        self.access_token = None
        self.user_id = None

    def print_banner(self):
        """Print welcome banner"""
        print()
        print("=" * 80)
        print("  SOCRATES2 - AI-Powered Specification Assistant")
        print("=" * 80)
        print()

    def check_setup(self):
        """Check if setup is complete"""
        print("[*] Checking project setup...")

        os.chdir(BACKEND_DIR)

        # Check .env file
        if not (BACKEND_DIR / ".env").exists():
            print("[!] .env file not found")
            response = input("[?] Create .env file now? (y/n): ").strip().lower()
            if response == 'y':
                print("[*] Creating .env file...")
                try:
                    subprocess.run(
                        [sys.executable, "scripts/setup_env.py"],
                        check=True
                    )
                    print("[OK] .env file created")
                except subprocess.CalledProcessError:
                    print("[ERROR] Failed to create .env file")
                    return False
            else:
                return False

        # Check dependencies
        print("[*] Verifying dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/verify_dependencies.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("[OK] All dependencies OK")
            else:
                print("[ERROR] Dependencies missing")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] Dependency check timed out")
            return False

        # Check database connections
        print("[*] Checking database connections...")
        try:
            from app.core.database import get_db_auth, get_db_specs
            try:
                get_db_auth()
                print("[OK] socrates_auth: Connected")
            except Exception as e:
                print("[ERROR] socrates_auth: {}".format(str(e)[:50]))
                return False
            try:
                get_db_specs()
                print("[OK] socrates_specs: Connected")
            except Exception as e:
                print("[ERROR] socrates_specs: {}".format(str(e)[:50]))
                return False
        except Exception:
            pass

        print()
        return True

    def start_server(self):
        """Start the FastAPI server in background"""
        print("[*] Starting API server in background...")

        os.chdir(BACKEND_DIR)

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host=0.0.0.0",
            "--port=8000",
            "--reload"
        ]

        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)  # Wait for server to start

            # Check if server is running
            try:
                response = requests.get(API_URL, timeout=2)
                print("[OK] Server running at {}".format(API_URL))
                print("[OK] API Docs:  {}/docs".format(API_URL))
                print()
                return True
            except Exception:
                print("[ERROR] Server failed to start")
                return False
        except Exception as e:
            print("[ERROR] Failed to start server: {}".format(e))
            return False

    def stop_server(self):
        """Stop the background server"""
        if self.server_process:
            print("[*] Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("[OK] Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("[OK] Server killed")
            self.server_process = None
        else:
            print("[!] No server running")

    def register(self, email: str, password: str):
        """Register a new user"""
        try:
            response = requests.post(
                "{}/api/v1/auth/register".format(API_URL),
                json={"email": email, "password": password},
                timeout=5
            )
            if response.status_code == 201:
                data = response.json()
                print("[OK] User registered: {}".format(email))
                print("     User ID: {}".format(data.get('id')))
                return True
            else:
                print("[ERROR] Registration failed: {}".format(response.text))
                return False
        except Exception as e:
            print("[ERROR] {}".format(e))
            return False

    def login(self, email: str, password: str):
        """Login user and get access token"""
        try:
            response = requests.post(
                "{}/api/v1/auth/login".format(API_URL),
                data={"username": email, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                print("[OK] Logged in as: {}".format(email))
                print("     Access Token: {}...".format(self.access_token[:20]))
                return True
            else:
                print("[ERROR] Login failed: {}".format(response.text))
                return False
        except Exception as e:
            print("[ERROR] {}".format(e))
            return False

    def get_headers(self):
        """Get authorization headers"""
        if self.access_token:
            return {"Authorization": "Bearer {}".format(self.access_token)}
        return {}

    def create_project(self, name: str, description: str):
        """Create a new project"""
        try:
            response = requests.post(
                "{}/api/v1/projects".format(API_URL),
                json={"name": name, "description": description},
                headers=self.get_headers(),
                timeout=5
            )
            if response.status_code in (200, 201):
                data = response.json()
                project_id = data.get('id')
                print("[OK] Project created: {}".format(name))
                print("     Project ID: {}".format(project_id))
                return project_id
            else:
                print("[ERROR] Failed to create project: {}".format(response.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def list_projects(self):
        """List all user projects"""
        try:
            response = requests.get(
                "{}/api/v1/projects".format(API_URL),
                headers=self.get_headers(),
                timeout=5
            )
            if response.status_code == 200:
                projects = response.json()
                print("[OK] Your Projects:")
                if isinstance(projects, list):
                    for p in projects:
                        print("     - {} (ID: {})".format(p.get('name'), p.get('id')))
                else:
                    print("     {}".format(projects))
                return projects
            else:
                print("[ERROR] {}".format(response.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def create_session(self, project_id: str, mode: str = "socratic"):
        """Create a session for a project"""
        try:
            response = requests.post(
                "{}/api/v1/projects/{}/sessions".format(API_URL, project_id),
                json={"mode": mode},
                headers=self.get_headers(),
                timeout=5
            )
            if response.status_code in (200, 201):
                data = response.json()
                session_id = data.get('id')
                print("[OK] Session created in {} mode".format(mode))
                print("     Session ID: {}".format(session_id))
                return session_id
            else:
                print("[ERROR] Failed to create session: {}".format(response.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def send_message(self, session_id: str, message: str):
        """Send a message in a session"""
        try:
            response = requests.post(
                "{}/api/v1/sessions/{}/message".format(API_URL, session_id),
                json={"message": message},
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response')
                print()
                print("[*] AI Response:")
                print("    {}".format(agent_response[:200]))
                print()
                return agent_response
            else:
                print("[ERROR] {}".format(response.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def print_help(self):
        """Print available commands"""
        print()
        print("=" * 80)
        print("  AVAILABLE COMMANDS")
        print("=" * 80)
        print()
        print("  AUTHENTICATION:")
        print("    register EMAIL PASSWORD      - Register new user")
        print("    login EMAIL PASSWORD         - Login user")
        print()
        print("  PROJECTS:")
        print("    projects                     - List your projects")
        print("    project-create NAME DESC     - Create a new project")
        print()
        print("  SESSIONS:")
        print("    session-create PROJECT_ID    - Create session (socratic mode)")
        print("    session-chat PROJECT_ID ID   - Send message to session")
        print()
        print("  PROJECT MANAGEMENT:")
        print("    test                         - Run all tests")
        print("    test-phase N                 - Run phase N tests")
        print("    health                       - Check API health")
        print("    status                       - Show git status")
        print()
        print("  SERVER:")
        print("    stop                         - Stop the API server")
        print()
        print("  OTHER:")
        print("    help                         - Show this help")
        print("    exit / quit                  - Exit the shell")
        print()
        print("  QUICK START EXAMPLE:")
        print("    1. register user@example.com password123")
        print("    2. login user@example.com password123")
        print("    3. project-create 'My Project' 'Test project'")
        print("    4. session-create PROJECT_ID")
        print("    5. session-chat SESSION_ID 'What are the main requirements?'")
        print()
        print("=" * 80)
        print()

    def handle_command(self, cmd_line: str):
        """Parse and execute a command"""
        if not cmd_line.strip():
            return

        parts = cmd_line.strip().split(None, 2)
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Authentication
        if cmd == 'register' and len(args) >= 2:
            email = args[0]
            password = args[1]
            self.register(email, password)

        elif cmd == 'login' and len(args) >= 2:
            email = args[0]
            password = args[1]
            self.login(email, password)

        # Projects
        elif cmd == 'projects':
            self.list_projects()

        elif cmd == 'project-create' and args:
            parts_full = cmd_line.strip().split(None, 1)
            if len(parts_full) > 1:
                remaining = parts_full[1]
                parts_split = remaining.split(None, 1)
                if len(parts_split) >= 2:
                    name = parts_split[0]
                    desc = parts_split[1]
                    self.create_project(name, desc)
                else:
                    print("[ERROR] Usage: project-create NAME DESCRIPTION")

        # Sessions
        elif cmd == 'session-create' and args:
            project_id = args[0]
            self.create_session(project_id)

        elif cmd == 'session-chat' and len(args) >= 2:
            session_id = args[0]
            message_parts = cmd_line.split(None, 2)
            if len(message_parts) >= 3:
                message = message_parts[2]
                self.send_message(session_id, message)
            else:
                print("[ERROR] Usage: session-chat SESSION_ID 'Your message'")

        # Testing
        elif cmd == 'test':
            print()
            print("[*] Running test suite...")
            os.chdir(BACKEND_DIR)
            subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"])
            print()

        elif cmd == 'test-phase' and args:
            phase = args[0]
            print()
            print("[*] Running Phase {} tests...".format(phase))
            os.chdir(BACKEND_DIR)
            subprocess.run([sys.executable, "-m", "pytest",
                           "tests/test_phase_{}_*.py".format(phase), "-v"])
            print()

        # Health
        elif cmd == 'health':
            print()
            try:
                response = requests.get("{}/api/v1/admin/health".format(API_URL), timeout=2)
                if response.status_code == 200:
                    print("[OK] API is healthy")
                    print(json.dumps(response.json(), indent=2))
                else:
                    print("[ERROR] API health check failed")
            except Exception as e:
                print("[ERROR] Cannot reach API: {}".format(e))
            print()

        # Status
        elif cmd == 'status':
            print()
            os.chdir(PROJECT_ROOT)
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print("[*] Git Status:")
                for line in result.stdout.strip().split('\n'):
                    print("    {}".format(line))
            else:
                print("[OK] Working directory clean")
            print()

        # Server
        elif cmd == 'stop':
            self.stop_server()
            self.running = False

        # Help
        elif cmd == 'help':
            self.print_help()

        # Exit
        elif cmd in ('exit', 'quit'):
            print("[*] Stopping server and exiting...")
            self.stop_server()
            print("[*] Goodbye!")
            self.running = False

        else:
            print("[ERROR] Unknown command: '{}'. Type 'help' for available commands.".format(cmd))

    def run(self):
        """Start the interactive shell"""
        self.print_banner()

        # Check setup
        if not self.check_setup():
            print("[!] Setup failed. Exiting.")
            sys.exit(1)

        # Start server
        print()
        if not self.start_server():
            print("[!] Failed to start server. Exiting.")
            sys.exit(1)

        # Print quick start
        print("=" * 80)
        print("  QUICK START")
        print("=" * 80)
        print()
        print("  1. Type 'help' to see all available commands")
        print("  2. Or open your browser: http://localhost:8000/docs")
        print()
        print("  Example workflow:")
        print("    socrates> register user@test.com mypassword")
        print("    socrates> login user@test.com mypassword")
        print("    socrates> project-create 'My Project' 'Testing'")
        print("    socrates> projects")
        print("    socrates> session-create <PROJECT_ID>")
        print("    socrates> session-chat <SESSION_ID> 'Hello, let's discuss requirements'")
        print()
        print("=" * 80)
        print()

        # Interactive loop
        while self.running:
            try:
                user_input = input("socrates> ").strip()
                if user_input:
                    self.handle_command(user_input)
            except KeyboardInterrupt:
                print()
                print("[*] Type 'exit' to quit")
            except EOFError:
                self.running = False


def main():
    """Main entry point"""
    app = SocratesApp()
    app.run()


if __name__ == "__main__":
    main()
