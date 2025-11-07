#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Socrates2 - Interactive Development Shell with Working Workflow

Usage:
    python Socrates.py        # Start server + interactive shell
"""

import subprocess
import sys
import os
import time
import requests
import json
import shlex
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

API_URL = "http://localhost:8000"


class SocratesApp:
    """Socrates2 Development Shell"""

    def __init__(self):
        self.running = True
        self.server_process = None
        self.access_token = None
        self.user_id = None
        self.current_project_id = None
        self.current_session_id = None

    def print_banner(self):
        print()
        print("=" * 80)
        print("  SOCRATES2 - AI-Powered Specification Assistant")
        print("=" * 80)
        print()

    def check_setup(self):
        print("[*] Checking project setup...")
        os.chdir(BACKEND_DIR)

        if not (BACKEND_DIR / ".env").exists():
            print("[!] .env file not found")
            response = input("[?] Create .env file now? (y/n): ").strip().lower()
            if response != 'y':
                return False
            print("[*] Creating .env file...")
            try:
                subprocess.run([sys.executable, "scripts/setup_env.py"], check=True)
                print("[OK] .env file created")
            except subprocess.CalledProcessError:
                print("[ERROR] Failed to create .env file")
                return False

        print("[*] Verifying dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/verify_dependencies.py"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print("[OK] All dependencies OK")
            else:
                print("[ERROR] Dependencies missing")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] Dependency check timed out")
            return False

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
        print("[*] Starting API server in background...")
        os.chdir(BACKEND_DIR)

        cmd = [sys.executable, "-m", "uvicorn", "app.main:app",
               "--host=0.0.0.0", "--port=8000", "--reload"]

        try:
            self.server_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            print("[*] Waiting for server to initialize...")
            for i in range(15):
                time.sleep(1)
                try:
                    response = requests.get(API_URL, timeout=1)
                    if response.status_code == 200:
                        print("[OK] Server running at {}".format(API_URL))
                        print("[OK] API Docs: {}/docs".format(API_URL))
                        print()
                        return True
                except Exception:
                    pass

            print("[ERROR] Server started but didn't respond")
            return False
        except Exception as e:
            print("[ERROR] Failed to start server: {}".format(e))
            return False

    def stop_server(self):
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

    def register(self, email, password):
        """Register a new user"""
        try:
            r = requests.post(
                "{}/api/v1/auth/register".format(API_URL),
                json={"email": email, "password": password}, timeout=5
            )
            if r.status_code in (200, 201):
                print("[OK] User registered: {}".format(email))
                return True
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return False
        except Exception as e:
            print("[ERROR] {}".format(e))
            return False

    def login(self, email, password):
        """Login and get access token"""
        try:
            r = requests.post(
                "{}/api/v1/auth/login".format(API_URL),
                data={"username": email, "password": password}, timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                self.access_token = data.get('access_token')
                self.user_id = data.get('user_id')
                print("[OK] Logged in as: {}".format(email))
                print("     User ID: {}".format(self.user_id))
                return True
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return False
        except Exception as e:
            print("[ERROR] {}".format(e))
            return False

    def get_headers(self):
        if self.access_token:
            return {"Authorization": "Bearer {}".format(self.access_token)}
        return {}

    def create_project(self, name, description):
        """Create a project"""
        try:
            r = requests.post(
                "{}/api/v1/projects".format(API_URL),
                json={"name": name, "description": description},
                headers=self.get_headers(), timeout=5
            )
            if r.status_code in (200, 201):
                data = r.json()
                self.current_project_id = data.get('id')
                print("[OK] Project created: {}".format(name))
                print("     ID: {}".format(self.current_project_id))
                return self.current_project_id
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def list_projects(self):
        """List projects"""
        try:
            r = requests.get(
                "{}/api/v1/projects".format(API_URL),
                headers=self.get_headers(), timeout=5
            )
            if r.status_code == 200:
                projects = r.json()
                print("[OK] Your Projects:")
                if isinstance(projects, list):
                    for p in projects:
                        print("     - {} (ID: {})".format(p.get('name'), p.get('id')))
                return projects
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def create_session(self, project_id):
        """Create a session"""
        try:
            r = requests.post(
                "{}/api/v1/projects/{}/sessions".format(API_URL, project_id),
                json={"mode": "socratic"},
                headers=self.get_headers(), timeout=5
            )
            if r.status_code in (200, 201):
                data = r.json()
                self.current_session_id = data.get('id')
                print("[OK] Session created")
                print("     ID: {}".format(self.current_session_id))
                return self.current_session_id
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def send_message(self, session_id, message):
        """Send a message"""
        try:
            r = requests.post(
                "{}/api/v1/sessions/{}/message".format(API_URL, session_id),
                json={"message": message},
                headers=self.get_headers(), timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                response = data.get('response')
                print("[*] AI Response:")
                print("    {}".format(response[:150]))
                return response
            else:
                print("[ERROR] {}".format(r.text[:100]))
                return None
        except Exception as e:
            print("[ERROR] {}".format(e))
            return None

    def print_help(self):
        print()
        print("=" * 80)
        print("  COMMANDS")
        print("=" * 80)
        print()
        print("  AUTH:")
        print("    register EMAIL PASSWORD        - Register user")
        print("    login EMAIL PASSWORD           - Login user")
        print()
        print("  PROJECTS:")
        print("    projects                       - List your projects")
        print("    create-project NAME DESC       - Create project")
        print()
        print("  SESSIONS:")
        print("    create-session [PROJECT_ID]    - Create session")
        print("    chat [SESSION_ID] MESSAGE      - Send message")
        print()
        print("  MANAGEMENT:")
        print("    test [PHASE]                   - Run tests")
        print("    health                         - API health check")
        print("    status                         - Git status")
        print()
        print("  OTHER:")
        print("    help                           - Show this help")
        print("    exit                           - Exit and stop server")
        print()
        print("=" * 80)
        print()

    def handle_command(self, line):
        """Handle user command"""
        if not line.strip():
            return

        try:
            # Try to parse as quoted command
            parts = shlex.split(line)
        except:
            # Fallback to simple split
            parts = line.strip().split(None, 3)

        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        # Auth
        if cmd == 'register':
            if len(args) >= 2:
                self.register(args[0], args[1])
            else:
                print("[!] Usage: register EMAIL PASSWORD")

        elif cmd == 'login':
            if len(args) >= 2:
                self.login(args[0], args[1])
            else:
                print("[!] Usage: login EMAIL PASSWORD")

        # Projects
        elif cmd == 'projects':
            self.list_projects()

        elif cmd == 'create-project':
            if len(args) >= 2:
                self.create_project(args[0], args[1])
            else:
                print("[!] Usage: create-project NAME DESCRIPTION")

        # Sessions
        elif cmd == 'create-session':
            project_id = args[0] if args else self.current_project_id
            if project_id:
                self.create_session(project_id)
            else:
                print("[!] Please provide PROJECT_ID or select a project first")

        elif cmd == 'chat':
            if len(args) >= 2:
                session_id = args[0]
                message = ' '.join(args[1:])
                self.send_message(session_id, message)
            elif len(args) == 1 and self.current_session_id:
                message = args[0]
                self.send_message(self.current_session_id, message)
            else:
                print("[!] Usage: chat [SESSION_ID] MESSAGE")

        # Testing
        elif cmd == 'test':
            print()
            os.chdir(BACKEND_DIR)
            if args and args[0].isdigit():
                phase = args[0]
                print("[*] Running Phase {} tests...".format(phase))
                subprocess.run([sys.executable, "-m", "pytest",
                               "tests/test_phase_{}_*.py".format(phase), "-q"])
            else:
                print("[*] Running all tests...")
                subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"])
            print()

        # Health
        elif cmd == 'health':
            print()
            try:
                r = requests.get("{}/api/v1/admin/health".format(API_URL), timeout=2)
                if r.status_code == 200:
                    print("[OK] API is healthy")
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
                capture_output=True, text=True
            )
            if result.stdout.strip():
                print("[*] Git Status:")
                for line in result.stdout.strip().split('\n'):
                    print("    {}".format(line))
            else:
                print("[OK] Working directory clean")
            print()

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
            print("[ERROR] Unknown command: '{}'. Type 'help' for help.".format(cmd))

    def run(self):
        self.print_banner()

        if not self.check_setup():
            print("[!] Setup failed.")
            sys.exit(1)

        print()
        if not self.start_server():
            print("[!] Failed to start server.")
            sys.exit(1)

        print("=" * 80)
        print("  QUICK START - Try This Workflow:")
        print("=" * 80)
        print()
        print("  1. register user@test.com mypassword")
        print("  2. login user@test.com mypassword")
        print("  3. create-project 'My Project' 'A test project'")
        print("  4. projects")
        print("  5. create-session <PROJECT_ID>")
        print("  6. chat <SESSION_ID> 'What are the main requirements?'")
        print("  7. chat 'What features should we build?'")
        print()
        print("  Type 'help' for all commands")
        print("=" * 80)
        print()

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
    app = SocratesApp()
    app.run()


if __name__ == "__main__":
    main()
