#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Socrates2 Interactive CLI - Main entry point for the Socrates2 project

Usage:
    python Socrates.py           # Start interactive shell (recommended)
    python Socrates.py start     # Start server directly
    python Socrates.py test      # Run tests
    python Socrates.py help      # Show available commands

The interactive shell automatically:
1. Checks and sets up .env if needed
2. Verifies all dependencies
3. Checks database connections
4. Provides a command prompt for project management
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

# Get project root
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Ensure backend is in path
sys.path.insert(0, str(BACKEND_DIR))


class SocratesShell:
    """Interactive shell for Socrates2 project management"""

    def __init__(self):
        self.running = True
        self.server_process = None

    def print_banner(self):
        """Print welcome banner"""
        print()
        print("=" * 70)
        print("  SOCRATES2 - AI-Powered Specification Assistant")
        print("=" * 70)
        print()
        print("  Type 'start' to launch the API server")
        print("  Type 'help'  to see all available commands")
        print()

    def check_and_setup(self):
        """Check if setup is needed and run it"""
        print("[*] Checking project setup...")
        print()

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
                print("[!] Setup skipped")
                return False
        else:
            print("[OK] .env file exists")

        # Verify dependencies
        print("[*] Verifying dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/verify_dependencies.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("[OK] All dependencies installed")
            else:
                print("[ERROR] Some dependencies missing")
                print(result.stdout)
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] Dependency check timed out")
            return False

        print()
        return True

    def check_database_connections(self):
        """Check if databases are accessible"""
        print("[*] Checking database connections...")
        print()

        try:
            from app.core.database import get_db_auth, get_db_specs

            auth_ok = False
            specs_ok = False

            try:
                auth_db = get_db_auth()
                print("[OK] socrates_auth: Connected")
                auth_ok = True
            except Exception as e:
                print("[ERROR] socrates_auth: {}".format(str(e)[:60]))

            try:
                specs_db = get_db_specs()
                print("[OK] socrates_specs: Connected")
                specs_ok = True
            except Exception as e:
                print("[ERROR] socrates_specs: {}".format(str(e)[:60]))

            print()
            return auth_ok and specs_ok

        except Exception as e:
            print("[ERROR] Failed to check connections: {}".format(e))
            print()
            return False

    def start_server(self):
        """Start the FastAPI server"""
        print()
        print("=" * 70)
        print("  STARTING SOCRATES2 API SERVER")
        print("=" * 70)
        print()
        print("  [*] Server URL:  http://localhost:8000")
        print("  [*] API Docs:    http://localhost:8000/docs")
        print("  [*] Health:      http://localhost:8000/api/v1/admin/health")
        print()
        print("  [*] Press Ctrl+C to stop the server and return to shell")
        print()
        print("=" * 70)
        print()

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
            self.server_process = subprocess.Popen(cmd)
            self.server_process.wait()
        except KeyboardInterrupt:
            print()
            print()
            print("[*] Server stopped. Returning to shell...")
            print()
        except Exception as e:
            print("[ERROR] Failed to start server: {}".format(e))
        finally:
            self.server_process = None

    def print_help(self):
        """Print available commands"""
        print()
        print("=" * 70)
        print("  AVAILABLE COMMANDS")
        print("=" * 70)
        print()
        print("  PROJECT & SERVER:")
        print("    start              Start the API server on http://localhost:8000")
        print("    stop               Stop a running server")
        print()
        print("  TESTING:")
        print("    test               Run all tests (144+ tests)")
        print("    test -v            Run tests with verbose output")
        print("    test-phase N       Run tests for phase N (e.g., test-phase 7)")
        print()
        print("  DATABASE:")
        print("    migrate            Run database migrations")
        print("    health             Check database connections and config")
        print()
        print("  INFORMATION:")
        print("    info               Show detailed project information")
        print("    status             Show git status and project stats")
        print("    docs               Show API documentation URLs")
        print("    setup              Setup .env and verify dependencies")
        print()
        print("  OTHER:")
        print("    help               Show this help message")
        print("    exit / quit        Exit the shell")
        print()
        print("=" * 70)
        print()

    def handle_command(self, cmd_line: str):
        """Parse and execute a command"""
        if not cmd_line.strip():
            return

        parts = cmd_line.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Server commands
        if cmd == 'start':
            self.start_server()

        elif cmd == 'stop':
            if self.server_process:
                print("[*] Stopping server...")
                self.server_process.terminate()
            else:
                print("[!] No server running")

        elif cmd == 'test':
            print()
            print("[*] Running test suite...")
            print()
            os.chdir(BACKEND_DIR)
            verbose = '-v' in args or '--verbose' in args

            cmd_list = [sys.executable, "-m", "pytest", "tests/"]
            if verbose:
                cmd_list.append("-v")
            else:
                cmd_list.append("-q")

            subprocess.run(cmd_list)
            print()

        elif cmd == 'test-phase' and args:
            phase = args[0]
            print()
            print("[*] Running Phase {} tests...".format(phase))
            print()
            os.chdir(BACKEND_DIR)

            cmd_list = [sys.executable, "-m", "pytest",
                       "tests/test_phase_{}_*.py".format(phase), "-v"]
            subprocess.run(cmd_list)
            print()

        elif cmd == 'migrate':
            print()
            print("[*] Running database migrations...")
            os.chdir(BACKEND_DIR)

            response = input("[?] Run migrations? (y/n): ").strip().lower()
            if response != 'y':
                print("[!] Migrations skipped")
                print()
                return

            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["powershell", "-ExecutionPolicy", "Bypass", "-File",
                         str(BACKEND_DIR / "scripts/run_migrations.ps1")],
                        check=True
                    )
                else:
                    subprocess.run(
                        ["bash", str(BACKEND_DIR / "scripts/run_migrations.ps1")],
                        check=True
                    )
                print("[OK] Migrations completed")
            except subprocess.CalledProcessError:
                print("[ERROR] Migration failed")
            print()

        elif cmd == 'health':
            print()
            print("[*] Checking Socrates2 Health...")
            print()
            os.chdir(BACKEND_DIR)

            try:
                from app.core.config import settings
                from app.core.database import get_db_auth, get_db_specs

                print("[*] Configuration:")
                print("    Environment: {}".format(settings.ENVIRONMENT))
                print("    Debug Mode:  {}".format(settings.DEBUG))
                print("    Log Level:   {}".format(settings.LOG_LEVEL))
                print()

                print("[*] Database Connections:")
                try:
                    auth_db = get_db_auth()
                    print("    [OK] socrates_auth: Connected")
                except Exception as e:
                    print("    [ERROR] socrates_auth: {}".format(str(e)[:50]))

                try:
                    specs_db = get_db_specs()
                    print("    [OK] socrates_specs: Connected")
                except Exception as e:
                    print("    [ERROR] socrates_specs: {}".format(str(e)[:50]))

                print()
            except Exception as e:
                print("[ERROR] {}".format(e))
                print()

        elif cmd == 'info':
            print()
            print("=" * 70)
            print("  SOCRATES2 PROJECT INFORMATION")
            print("=" * 70)
            print()
            print("[*] Project Details:")
            print("    Version:         0.1.0")
            print("    Implementation:  Phases 1-9 (Complete)")
            print("    Status:          Active Development")
            print("    Framework:       FastAPI (Python 3.12)")
            print()
            print("[*] Databases:")
            print("    * socrates_auth:  User authentication & profiles")
            print("    * socrates_specs: Projects, specs, conversations")
            print()
            print("[*] Registered Agents (12 Total):")
            agents = [
                "Project Manager", "Socratic Counselor", "Context Analyzer",
                "Conflict Detector", "Code Generator", "Quality Controller",
                "User Learning", "Direct Chat", "Team Collaboration",
                "Export Agent", "Multi-LLM Manager", "GitHub Integration"
            ]
            for i, agent in enumerate(agents, 1):
                print("    {}. {}".format(i, agent))
            print()
            print("[*] Test Coverage:")
            print("    Total Tests:  144+ tests")
            print("    Phases:       All phases (1-9)")
            print("    Migrations:   19 database migrations")
            print()
            print("[*] Project Location:")
            print("    {}".format(PROJECT_ROOT))
            print()
            print("=" * 70)
            print()

        elif cmd == 'status':
            print()
            print("=" * 70)
            print("  PROJECT STATUS")
            print("=" * 70)
            print()
            os.chdir(PROJECT_ROOT)

            # Git status
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print("[*] Git Status:")
                    if result.stdout.strip():
                        for line in result.stdout.strip().split('\n'):
                            print("    {}".format(line))
                    else:
                        print("    Clean [OK]")
                    print()
            except Exception:
                pass

            # Branch
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
                    print("[*] Current Branch: {}".format(branch))
                    print()
            except Exception:
                pass

            print("=" * 70)
            print()

        elif cmd == 'docs':
            print()
            print("=" * 70)
            print("  API DOCUMENTATION")
            print("=" * 70)
            print()
            print("[*] Start the server first:")
            print("    Command: start")
            print()
            print("[*] Then open in your browser:")
            print()
            print("    Interactive Docs (Swagger UI):")
            print("      http://localhost:8000/docs")
            print()
            print("    Alternative Docs (ReDoc):")
            print("      http://localhost:8000/redoc")
            print()
            print("    OpenAPI Schema (JSON):")
            print("      http://localhost:8000/openapi.json")
            print()
            print("[*] Key API Endpoints:")
            print("    GET  /                    - API root")
            print("    GET  /api/v1/info         - API information")
            print("    GET  /api/v1/admin/health - Health check")
            print("    POST /api/v1/auth/register - User registration")
            print("    POST /api/v1/auth/login    - User login")
            print()
            print("=" * 70)
            print()

        elif cmd == 'setup':
            print()
            self.check_and_setup()

        elif cmd == 'help':
            self.print_help()

        elif cmd in ('exit', 'quit'):
            print("[*] Goodbye!")
            self.running = False

        else:
            print("[ERROR] Unknown command: '{}'. Type 'help' for available commands.".format(cmd))
            print()

    def run(self):
        """Start the interactive shell"""
        self.print_banner()

        # Auto-check setup on startup
        if not self.check_and_setup():
            print("[!] Setup incomplete. Exiting.")
            sys.exit(1)

        # Check database connections
        if not self.check_database_connections():
            print("[!] Database connections failed.")
            print("[*] Try running: migrate")
            print()

        # Main interactive loop
        while self.running:
            try:
                user_input = input("socrates> ").strip()
                if user_input:
                    self.handle_command(user_input)
            except KeyboardInterrupt:
                print()
                print("[*] Type 'exit' to quit, or continue with another command")
                print()
            except EOFError:
                print()
                self.running = False


def main():
    """Main entry point"""
    # If arguments provided, run legacy CLI mode
    if len(sys.argv) > 1:
        # Parse command
        cmd = sys.argv[1].lower()

        if cmd == '--version':
            print("Socrates2, version 0.1.0")
        elif cmd == '--help':
            print("Usage: python Socrates.py [COMMAND]")
            print()
            print("Without arguments, starts the interactive shell.")
            print()
            print("Commands:")
            print("  start         Start API server")
            print("  test          Run tests")
            print("  test-phase N  Run phase tests")
            print("  migrate       Run migrations")
            print("  health        Check health")
            print("  info          Show info")
            print("  status        Show status")
            print("  docs          Show docs")
            print("  setup         Setup project")
            print("  help          Show help")
            print("  exit          Exit shell")
        else:
            # Start shell and execute command
            shell = SocratesShell()
            shell.print_banner()

            if not shell.check_and_setup():
                print("[!] Setup incomplete. Exiting.")
                sys.exit(1)

            shell.check_database_connections()
            shell.handle_command(" ".join(sys.argv[1:]))
            sys.exit(0)
    else:
        # Interactive shell mode (default)
        shell = SocratesShell()
        shell.run()


if __name__ == "__main__":
    main()
