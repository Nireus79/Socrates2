#!/usr/bin/env python3
"""
Socrates CLI Workflow Tests

Comprehensive end-to-end workflow tests that simulate real user experiences.
Tests the complete user journey from registration to project management.

Usage:
    python test_cli_workflow.py              # Run all workflow tests
    python test_cli_workflow.py --verbose    # Verbose output with details
"""

import sys
import os
import requests
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Error: rich library not installed")
    print("Install with: pip install rich")
    sys.exit(1)


class WorkflowTester:
    """Comprehensive workflow tester for Socrates CLI"""

    def __init__(self, api_url: str = "http://localhost:8000", verbose: bool = False):
        self.api_url = api_url
        self.verbose = verbose
        self.console = Console()

        # Test data
        self.test_username = f"workflow_test_{uuid.uuid4().hex[:8]}"
        self.test_email = f"{self.test_username}@example.com"
        self.test_password = "TestPassword123!"
        self.test_name = "Workflow"
        self.test_surname = "Tester"

        # State
        self.access_token = None
        self.user_id = None
        self.project_id = None
        self.session_id = None

        # Results
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.issues_found = []

    def log(self, message: str, level: str = "info"):
        """Log message with color"""
        colors = {
            "info": "cyan",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "debug": "dim"
        }
        color = colors.get(level, "white")
        self.console.print(f"[{color}]{message}[/{color}]")

    def debug(self, message: str):
        """Log debug message if verbose"""
        if self.verbose:
            self.log(f"  DEBUG: {message}", "debug")

    def api_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """
        Make API request and return (success, status_code, data)

        Returns:
            (bool, int, dict): (success, status_code, response_data)
        """
        url = f"{self.api_url}{endpoint}"

        # Add auth header if token available
        if self.access_token and 'headers' not in kwargs:
            kwargs['headers'] = {"Authorization": f"Bearer {self.access_token}"}
        elif self.access_token and 'Authorization' not in kwargs.get('headers', {}):
            kwargs.setdefault('headers', {})
            kwargs['headers']["Authorization"] = f"Bearer {self.access_token}"

        self.debug(f"{method} {url}")
        if kwargs.get('json'):
            self.debug(f"  JSON: {kwargs['json']}")
        if kwargs.get('data'):
            self.debug(f"  DATA: {kwargs['data']}")

        try:
            response = requests.request(method, url, **kwargs, timeout=10)

            self.debug(f"  Status: {response.status_code}")

            # Try to parse JSON
            try:
                data = response.json()
                self.debug(f"  Response: {data}")
            except:
                data = {"detail": response.text}

            success = 200 <= response.status_code < 300
            return success, response.status_code, data

        except requests.exceptions.ConnectionError:
            self.log(f"[X] Cannot connect to {self.api_url}", "error")
            self.log("  Make sure backend is running:", "warning")
            self.log("    cd backend && uvicorn app.main:app --reload", "warning")
            return False, 0, {"detail": "Connection refused"}
        except Exception as e:
            self.log(f"✗ Request error: {e}", "error")
            return False, 0, {"detail": str(e)}

    def test_step(self, name: str, test_func):
        """Run a test step and track results"""
        self.tests_run += 1
        self.console.print(f"\n[bold cyan]Test {self.tests_run}: {name}[/bold cyan]")

        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                self.log("  [OK] PASSED", "success")
                return True
            else:
                self.tests_failed += 1
                self.log("  [X] FAILED", "error")
                return False
        except Exception as e:
            self.tests_failed += 1
            self.log(f"  [X] EXCEPTION: {e}", "error")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def add_issue(self, issue: str, severity: str = "medium", recommendation: str = ""):
        """Record an issue found during testing"""
        self.issues_found.append({
            "issue": issue,
            "severity": severity,
            "recommendation": recommendation
        })

    # ========== WORKFLOW TESTS ==========

    def test_user_registration(self) -> bool:
        """Test user registration workflow"""
        success, status, data = self.api_request(
            "POST",
            "/api/v1/auth/register",
            json={
                "name": self.test_name,
                "surname": self.test_surname,
                "username": self.test_username,
                "password": self.test_password,
                "email": self.test_email
            }
        )

        if not success:
            self.add_issue(
                f"Registration failed with status {status}: {data.get('detail')}",
                severity="high",
                recommendation="Check auth.py register endpoint and database connection"
            )
            return False

        # Check response format
        if "user_id" not in data:
            self.add_issue(
                "Registration response missing 'user_id' field",
                severity="high",
                recommendation="CLI expects 'user_id' in response - check RegisterResponse schema"
            )
            return False

        if "email" not in data:
            self.add_issue(
                "Registration response missing 'email' field",
                severity="medium"
            )

        self.user_id = data.get("user_id")
        self.log(f"  User ID: {self.user_id}", "success")

        return True

    def test_user_login(self) -> bool:
        """Test user login workflow (OAuth2 format)"""
        success, status, data = self.api_request(
            "POST",
            "/api/v1/auth/login",
            data={
                "username": self.test_username,  # OAuth2 uses 'username' field
                "password": self.test_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if not success:
            self.add_issue(
                f"Login failed with status {status}: {data.get('detail')}",
                severity="high",
                recommendation="Check OAuth2PasswordRequestForm in auth.py"
            )
            return False

        # Check response format
        if "access_token" not in data:
            self.add_issue(
                "Login response missing 'access_token'",
                severity="high",
                recommendation="CLI cannot authenticate without access_token"
            )
            return False

        self.access_token = data.get("access_token")
        self.log(f"  Token: {self.access_token[:20]}...", "success")

        return True

    def test_project_creation(self) -> bool:
        """Test project creation workflow"""
        if not self.access_token:
            self.log("  Skipping: Not logged in", "warning")
            return False

        success, status, data = self.api_request(
            "POST",
            "/api/v1/projects",
            json={
                "name": "Workflow Test Project",
                "description": "Created by workflow tester"
            }
        )

        if not success:
            self.add_issue(
                f"Project creation failed with status {status}: {data.get('detail')}",
                severity="high",
                recommendation=f"Check projects.py endpoint. Status: {status}, Response: {data}"
            )

            # Specific debugging for 404
            if status == 404:
                self.add_issue(
                    "Endpoint not found (404) - this is what the user is seeing!",
                    severity="critical",
                    recommendation="Check if router is properly included in main.py and prefix is correct"
                )

            return False

        # Check response format (what CLI expects)
        if "success" not in data:
            self.add_issue(
                "Project creation response missing 'success' field",
                severity="high",
                recommendation="CLI line 467 checks result.get('success') - add this field"
            )

        if "project_id" not in data:
            self.add_issue(
                "Project creation response missing 'project_id' field",
                severity="high",
                recommendation="CLI line 468 expects project_id"
            )
            return False

        self.project_id = data.get("project_id")
        self.log(f"  Project ID: {self.project_id}", "success")

        return data.get("success", False)

    def test_list_projects(self) -> bool:
        """Test listing projects"""
        if not self.access_token:
            self.log("  Skipping: Not logged in", "warning")
            return False

        success, status, data = self.api_request(
            "GET",
            "/api/v1/projects?skip=0&limit=100"
        )

        if not success:
            self.add_issue(
                f"List projects failed with status {status}",
                severity="medium"
            )
            return False

        # Check response format
        if "projects" not in data:
            self.add_issue(
                "List projects response missing 'projects' array",
                severity="high"
            )
            return False

        projects = data.get("projects", [])
        if not isinstance(projects, list):
            self.add_issue(
                "'projects' field is not an array",
                severity="high"
            )
            return False

        # Check if our project is in the list
        found = any(p.get("id") == self.project_id for p in projects)
        if not found and self.project_id:
            self.add_issue(
                "Created project not found in list",
                severity="high"
            )
            return False

        self.log(f"  Found {len(projects)} project(s)", "success")
        return True

    def test_get_project_details(self) -> bool:
        """Test getting project details"""
        if not self.access_token or not self.project_id:
            self.log("  Skipping: No project created", "warning")
            return False

        success, status, data = self.api_request(
            "GET",
            f"/api/v1/projects/{self.project_id}"
        )

        if not success:
            self.add_issue(
                f"Get project failed with status {status}",
                severity="medium"
            )
            return False

        # Check response format (CLI line 489 expects)
        if "success" not in data:
            self.add_issue(
                "Get project response missing 'success' field",
                severity="medium",
                recommendation="CLI line 489 checks result.get('success')"
            )

        if "project" not in data:
            self.add_issue(
                "Get project response missing 'project' field",
                severity="high",
                recommendation="CLI line 490 expects project data"
            )
            return False

        return data.get("success", False)

    def test_start_session(self) -> bool:
        """Test starting a Socratic session"""
        if not self.access_token or not self.project_id:
            self.log("  Skipping: No project created", "warning")
            return False

        success, status, data = self.api_request(
            "POST",
            f"/api/v1/projects/{self.project_id}/sessions"
        )

        if not success:
            self.add_issue(
                f"Start session failed with status {status}",
                severity="medium"
            )
            return False

        # Check response format
        if "success" not in data:
            self.add_issue(
                "Start session response missing 'success' field",
                severity="medium"
            )

        if "session" not in data:
            self.add_issue(
                "Start session response missing 'session' field",
                severity="high"
            )
            return False

        session = data.get("session", {})
        self.session_id = session.get("id")

        if not self.session_id:
            self.add_issue(
                "Session object missing 'id' field",
                severity="high"
            )
            return False

        self.log(f"  Session ID: {self.session_id}", "success")
        return True

    def test_get_next_question(self) -> bool:
        """Test getting next Socratic question"""
        if not self.session_id:
            self.log("  Skipping: No session started", "warning")
            return False

        success, status, data = self.api_request(
            "POST",
            f"/api/v1/sessions/{self.session_id}/next-question",
            json={"context": {}}
        )

        if not success:
            self.add_issue(
                f"Get next question failed with status {status}",
                severity="medium"
            )
            return False

        # Check response format
        if "question" not in data:
            self.add_issue(
                "Next question response missing 'question' field",
                severity="high"
            )
            return False

        if "question_id" not in data:
            self.add_issue(
                "Next question response missing 'question_id' field",
                severity="high"
            )
            return False

        self.log(f"  Question: {data['question'][:60]}...", "success")
        return True

    def test_cleanup(self) -> bool:
        """Clean up test data"""
        if not self.access_token or not self.project_id:
            return True

        success, status, data = self.api_request(
            "DELETE",
            f"/api/v1/projects/{self.project_id}"
        )

        if not success:
            self.log(f"  Warning: Could not delete test project", "warning")

        return True

    # ========== MAIN TEST RUNNER ==========

    def run_all_workflows(self) -> bool:
        """Run all workflow tests"""
        self.console.print("\n[bold]=" * 40 + "[/bold]")
        self.console.print("[bold cyan]  Socrates CLI Workflow Tests[/bold cyan]")
        self.console.print("[bold]=" * 40 + "[/bold]\n")

        # Check if backend is running
        try:
            response = requests.get(f"{self.api_url}/docs", timeout=2)
            if response.status_code != 200:
                self.log("[X] Backend not responding correctly", "error")
                return False
        except:
            self.log(f"[X] Backend not running at {self.api_url}", "error")
            self.log("  Start with: cd backend && uvicorn app.main:app --reload", "warning")
            return False

        self.log(f"[OK] Backend is running at {self.api_url}", "success")

        # Run tests in order
        tests = [
            ("User Registration", self.test_user_registration),
            ("User Login (OAuth2)", self.test_user_login),
            ("Project Creation", self.test_project_creation),
            ("List Projects", self.test_list_projects),
            ("Get Project Details", self.test_get_project_details),
            ("Start Session", self.test_start_session),
            ("Get Next Question", self.test_get_next_question),
            ("Cleanup", self.test_cleanup),
        ]

        for name, test_func in tests:
            self.test_step(name, test_func)
            time.sleep(0.3)  # Small delay between tests

        # Print summary
        self.print_summary()

        return self.tests_failed == 0

    def print_summary(self):
        """Print test summary"""
        self.console.print("\n[bold]=" * 40 + "[/bold]")
        self.console.print("[bold cyan]  Summary[/bold cyan]")
        self.console.print("[bold]=" * 40 + "[/bold]\n")

        # Test results
        total = self.tests_run
        passed = self.tests_passed
        failed = self.tests_failed
        success_rate = (passed / total * 100) if total > 0 else 0

        self.console.print(f"Tests Run:    {total}")
        self.console.print(f"[green]Passed:       {passed}[/green]")
        self.console.print(f"[red]Failed:       {failed}[/red]")
        self.console.print(f"Success Rate: {success_rate:.1f}%")

        # Issues found
        if self.issues_found:
            self.console.print(f"\n[bold red]Issues Found: {len(self.issues_found)}[/bold red]\n")

            # Group by severity
            critical = [i for i in self.issues_found if i['severity'] == 'critical']
            high = [i for i in self.issues_found if i['severity'] == 'high']
            medium = [i for i in self.issues_found if i['severity'] == 'medium']
            low = [i for i in self.issues_found if i['severity'] == 'low']

            for severity, issues in [('Critical', critical), ('High', high), ('Medium', medium), ('Low', low)]:
                if issues:
                    color = {'Critical': 'red', 'High': 'red', 'Medium': 'yellow', 'Low': 'cyan'}[severity]
                    self.console.print(f"[bold {color}]{severity} Priority:[/bold {color}]")
                    for i, issue in enumerate(issues, 1):
                        self.console.print(f"  {i}. {issue['issue']}")
                        if issue.get('recommendation'):
                            self.console.print(f"     [dim]-> {issue['recommendation']}[/dim]")
                    print()

        else:
            self.console.print("\n[green][OK] No issues found![/green]")

        # Final status
        print()
        if failed == 0:
            self.console.print("[bold green][OK] ALL WORKFLOWS PASSED[/bold green]")
        else:
            self.console.print("[bold red][X] SOME WORKFLOWS FAILED[/bold red]")
            self.console.print("[yellow]Review issues above and fix the problems[/yellow]")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Socrates CLI Workflow Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='Backend API URL')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output with debug info')

    args = parser.parse_args()

    tester = WorkflowTester(api_url=args.api_url, verbose=args.verbose)
    success = tester.run_all_workflows()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
