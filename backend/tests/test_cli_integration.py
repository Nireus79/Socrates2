"""
Socrates CLI Integration Tests

Tests CLI with actual backend API.
Requires backend server running at http://localhost:8000
"""

import sys
import os
import requests
import time
import uuid
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Socrates import SocratesAPI
from rich.console import Console


class CLIIntegrationTest:
    """Integration test runner for CLI"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.console = Console()
        self.api = SocratesAPI(api_url, self.console)
        self.test_user_email = f"test_{uuid.uuid4().hex[:8]}@socrates.test"
        self.test_password = "TestPass123!"
        self.access_token = None
        self.test_project_id = None
        self.test_session_id = None
        self.passed = 0
        self.failed = 0

    def log(self, message: str, level: str = "info"):
        """Log test message"""
        colors = {
            "info": "cyan",
            "success": "green",
            "error": "red",
            "warning": "yellow"
        }
        self.console.print(f"[{colors.get(level, 'white')}]{message}[/{colors.get(level, 'white')}]")

    def check_backend(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.api_url}/docs", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def assert_true(self, condition: bool, message: str):
        """Assert condition is true"""
        if condition:
            self.log(f"  ✓ {message}", "success")
            self.passed += 1
        else:
            self.log(f"  ✗ {message}", "error")
            self.failed += 1
            raise AssertionError(message)

    def assert_in(self, item: str, container: Any, message: str):
        """Assert item is in container"""
        if item in container:
            self.log(f"  ✓ {message}", "success")
            self.passed += 1
        else:
            self.log(f"  ✗ {message} (expected '{item}' in {container})", "error")
            self.failed += 1
            raise AssertionError(message)

    def test_1_registration(self):
        """Test 1: User Registration"""
        self.log("\n[bold]Test 1: User Registration[/bold]")

        try:
            result = self.api.register(self.test_user_email, self.test_password)

            self.assert_in("user_id", result, "Response contains user_id")
            self.assert_in("email", result, "Response contains email")
            self.assert_true(result["email"] == self.test_user_email, "Email matches")
            self.assert_in("message", result, "Response contains message")

            self.log(f"  → Created user: {result['user_id'][:16]}...")
        except Exception as e:
            self.log(f"  ✗ Registration failed: {e}", "error")
            self.failed += 1
            raise

    def test_2_duplicate_registration(self):
        """Test 2: Duplicate Registration (Should Fail)"""
        self.log("\n[bold]Test 2: Duplicate Registration[/bold]")

        try:
            result = self.api.register(self.test_user_email, self.test_password)
            self.log(f"  ✗ Should have failed but got: {result}", "error")
            self.failed += 1
        except Exception as e:
            # Should raise exception for duplicate email
            self.log(f"  ✓ Correctly rejected duplicate: {str(e)[:50]}...", "success")
            self.passed += 1

    def test_3_login(self):
        """Test 3: User Login"""
        self.log("\n[bold]Test 3: User Login[/bold]")

        try:
            result = self.api.login(self.test_user_email, self.test_password)

            self.assert_in("access_token", result, "Response contains access_token")
            self.assert_in("user_id", result, "Response contains user_id")
            self.assert_in("email", result, "Response contains email")
            self.assert_true(result["token_type"] == "bearer", "Token type is bearer")

            self.access_token = result["access_token"]
            self.api.set_token(self.access_token)
            self.log(f"  → Token: {self.access_token[:20]}...")
        except Exception as e:
            self.log(f"  ✗ Login failed: {e}", "error")
            self.failed += 1
            raise

    def test_4_invalid_login(self):
        """Test 4: Invalid Login (Should Fail)"""
        self.log("\n[bold]Test 4: Invalid Login[/bold]")

        try:
            result = self.api.login(self.test_user_email, "WrongPassword!")
            self.log(f"  ✗ Should have failed but got: {result}", "error")
            self.failed += 1
        except Exception:
            self.log("  ✓ Correctly rejected invalid credentials", "success")
            self.passed += 1

    def test_5_create_project(self):
        """Test 5: Create Project"""
        self.log("\n[bold]Test 5: Create Project[/bold]")

        if not self.access_token:
            self.log("  ⚠ Skipping (not logged in)", "warning")
            return

        try:
            result = self.api.create_project(
                "Test Project CLI",
                "Integration test project from CLI"
            )

            self.assert_in("success", result, "Response contains success field")
            self.assert_true(result["success"], "Success is true")
            self.assert_in("project_id", result, "Response contains project_id")

            self.test_project_id = result["project_id"]
            self.log(f"  → Created project: {self.test_project_id[:16]}...")
        except Exception as e:
            self.log(f"  ✗ Project creation failed: {e}", "error")
            self.failed += 1
            raise

    def test_6_list_projects(self):
        """Test 6: List Projects"""
        self.log("\n[bold]Test 6: List Projects[/bold]")

        if not self.access_token:
            self.log("  ⚠ Skipping (not logged in)", "warning")
            return

        try:
            result = self.api.list_projects()

            self.assert_in("projects", result, "Response contains projects list")
            self.assert_true(isinstance(result["projects"], list), "Projects is a list")
            self.assert_true(len(result["projects"]) > 0, "At least one project exists")

            # Find our test project
            found = any(p["id"] == self.test_project_id for p in result["projects"])
            self.assert_true(found, "Our test project is in the list")

            self.log(f"  → Found {len(result['projects'])} project(s)")
        except Exception as e:
            self.log(f"  ✗ List projects failed: {e}", "error")
            self.failed += 1
            raise

    def test_7_get_project(self):
        """Test 7: Get Project Details"""
        self.log("\n[bold]Test 7: Get Project Details[/bold]")

        if not self.test_project_id:
            self.log("  ⚠ Skipping (no project created)", "warning")
            return

        try:
            result = self.api.get_project(self.test_project_id)

            self.assert_in("success", result, "Response contains success field")
            self.assert_in("project", result, "Response contains project data")

            project = result["project"]
            self.assert_true(project["id"] == self.test_project_id, "Project ID matches")
            self.assert_true(project["name"] == "Test Project CLI", "Project name matches")

            self.log(f"  → Project: {project['name']}")
            self.log(f"  → Phase: {project.get('current_phase', 'N/A')}")
            self.log(f"  → Maturity: {project.get('maturity_score', 0):.1f}%")
        except Exception as e:
            self.log(f"  ✗ Get project failed: {e}", "error")
            self.failed += 1
            raise

    def test_8_start_session(self):
        """Test 8: Start Socratic Session"""
        self.log("\n[bold]Test 8: Start Socratic Session[/bold]")

        if not self.test_project_id:
            self.log("  ⚠ Skipping (no project created)", "warning")
            return

        try:
            result = self.api.start_session(self.test_project_id)

            self.assert_in("success", result, "Response contains success field")
            self.assert_in("session", result, "Response contains session data")

            session = result["session"]
            self.test_session_id = session["id"]
            self.assert_true(session["status"] == "active", "Session status is active")

            self.log(f"  → Session: {self.test_session_id[:16]}...")
        except Exception as e:
            self.log(f"  ✗ Start session failed: {e}", "error")
            self.failed += 1
            raise

    def test_9_get_next_question(self):
        """Test 9: Get Next Socratic Question"""
        self.log("\n[bold]Test 9: Get Next Socratic Question[/bold]")

        if not self.test_session_id:
            self.log("  ⚠ Skipping (no session started)", "warning")
            return

        try:
            result = self.api.get_next_question(self.test_session_id)

            self.assert_in("success", result, "Response contains success field")
            self.assert_in("question", result, "Response contains question")
            self.assert_in("question_id", result, "Response contains question_id")

            self.log(f"  → Question: {result['question'][:60]}...")
        except Exception as e:
            self.log(f"  ✗ Get next question failed: {e}", "error")
            self.failed += 1
            raise

    def test_10_submit_answer(self):
        """Test 10: Submit Answer to Socratic Question"""
        self.log("\n[bold]Test 10: Submit Answer[/bold]")

        if not self.test_session_id:
            self.log("  ⚠ Skipping (no session started)", "warning")
            return

        try:
            # Get a question first
            question_result = self.api.get_next_question(self.test_session_id)
            question_id = question_result["question_id"]

            # Submit answer
            result = self.api.submit_answer(
                self.test_session_id,
                question_id,
                "I want to build a REST API for managing customer data with authentication and CRUD operations"
            )

            self.assert_in("success", result, "Response contains success field")

            if "specs_extracted" in result:
                self.log(f"  → Extracted {len(result['specs_extracted'])} spec(s)")

        except Exception as e:
            self.log(f"  ✗ Submit answer failed: {e}", "error")
            self.failed += 1
            raise

    def test_11_list_sessions(self):
        """Test 11: List Sessions"""
        self.log("\n[bold]Test 11: List Sessions[/bold]")

        if not self.test_project_id:
            self.log("  ⚠ Skipping (no project created)", "warning")
            return

        try:
            result = self.api.list_sessions(self.test_project_id)

            self.assert_in("sessions", result, "Response contains sessions list")
            self.assert_true(isinstance(result["sessions"], list), "Sessions is a list")
            self.assert_true(len(result["sessions"]) > 0, "At least one session exists")

            self.log(f"  → Found {len(result['sessions'])} session(s)")
        except Exception as e:
            self.log(f"  ✗ List sessions failed: {e}", "error")
            self.failed += 1
            raise

    def test_12_get_session_history(self):
        """Test 12: Get Session History"""
        self.log("\n[bold]Test 12: Get Session History[/bold]")

        if not self.test_session_id:
            self.log("  ⚠ Skipping (no session started)", "warning")
            return

        try:
            result = self.api.get_session_history(self.test_session_id)

            self.assert_in("success", result, "Response contains success field")
            self.assert_in("conversation_history", result, "Response contains history")

            history = result["conversation_history"]
            self.assert_true(isinstance(history, list), "History is a list")

            self.log(f"  → History has {len(history)} entries")
        except Exception as e:
            self.log(f"  ✗ Get session history failed: {e}", "error")
            self.failed += 1
            raise

    def test_13_end_session(self):
        """Test 13: End Session"""
        self.log("\n[bold]Test 13: End Session[/bold]")

        if not self.test_session_id:
            self.log("  ⚠ Skipping (no session started)", "warning")
            return

        try:
            result = self.api.end_session(self.test_session_id)

            self.assert_in("success", result, "Response contains success field")

            if "specs_count" in result:
                self.log(f"  → Session ended with {result['specs_count']} specs")

        except Exception as e:
            self.log(f"  ✗ End session failed: {e}", "error")
            self.failed += 1
            raise

    def test_14_delete_project(self):
        """Test 14: Delete Project"""
        self.log("\n[bold]Test 14: Delete Project (Cleanup)[/bold]")

        if not self.test_project_id:
            self.log("  ⚠ Skipping (no project created)", "warning")
            return

        try:
            result = self.api.delete_project(self.test_project_id)

            self.assert_in("success", result, "Response contains success field")
            self.log("  → Project deleted successfully")

        except Exception as e:
            self.log(f"  ✗ Delete project failed: {e}", "error")
            self.failed += 1

    def test_15_logout(self):
        """Test 15: Logout"""
        self.log("\n[bold]Test 15: Logout[/bold]")

        if not self.access_token:
            self.log("  ⚠ Skipping (not logged in)", "warning")
            return

        try:
            result = self.api.logout()
            self.log("  ✓ Logged out successfully", "success")
            self.passed += 1
        except Exception as e:
            self.log(f"  ✗ Logout failed: {e}", "error")
            self.failed += 1

    def run_all_tests(self):
        """Run all integration tests"""
        self.console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
        self.console.print("[bold cyan]   Socrates CLI Integration Tests[/bold cyan]")
        self.console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

        # Check backend
        self.log("Checking backend connection...")
        if not self.check_backend():
            self.log("✗ Backend not running at " + self.api_url, "error")
            self.log("  Start backend with: cd backend && uvicorn app.main:app --reload", "warning")
            return False

        self.log(f"✓ Backend is running at {self.api_url}", "success")

        # Run tests in order
        tests = [
            self.test_1_registration,
            self.test_2_duplicate_registration,
            self.test_3_login,
            self.test_4_invalid_login,
            self.test_5_create_project,
            self.test_6_list_projects,
            self.test_7_get_project,
            self.test_8_start_session,
            self.test_9_get_next_question,
            self.test_10_submit_answer,
            self.test_11_list_sessions,
            self.test_12_get_session_history,
            self.test_13_end_session,
            self.test_14_delete_project,
            self.test_15_logout
        ]

        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log(f"\n[bold red]Test failed with error: {e}[/bold red]", "error")
                if self.console.input("\nContinue with remaining tests? (y/n): ").lower() != 'y':
                    break

        # Summary
        self.console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
        self.console.print("[bold]Test Summary[/bold]")
        self.console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
        self.console.print(f"[green]Passed: {self.passed}[/green]")
        self.console.print(f"[red]Failed: {self.failed}[/red]")
        total = self.passed + self.failed
        if total > 0:
            percentage = (self.passed / total) * 100
            self.console.print(f"[bold]Success Rate: {percentage:.1f}%[/bold]\n")

        return self.failed == 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Socrates CLI Integration Tests")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Socrates API URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    tester = CLIIntegrationTest(api_url=args.api_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
