#!/usr/bin/env python3
"""
Socrates2 Master Test Runner

Comprehensive test suite for all Socrates components:
- Backend API tests
- CLI tests
- Agent tests
- Database tests
- Integration tests
- Performance tests
- Security tests

Usage:
    python run_all_tests.py                  # Run all tests
    python run_all_tests.py --fast           # Run only fast tests
    python run_all_tests.py --category api   # Run specific category
    python run_all_tests.py --coverage       # Run with coverage report
    python run_all_tests.py --verbose        # Verbose output
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Master test runner for Socrates2"""

    def __init__(self, verbose: bool = False, coverage: bool = False):
        self.verbose = verbose
        self.coverage = coverage
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.results = {}
        self.start_time = None
        self.end_time = None

    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

    def print_section(self, text: str):
        """Print formatted section"""
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'-' * len(text)}{Colors.ENDC}")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

    def print_failure(self, text: str):
        """Print failure message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self.print_section("Checking Dependencies")

        required = {
            'pytest': 'pytest',
            'pytest-asyncio': 'pytest_asyncio',
            'pytest-cov': 'pytest_cov',
            'requests': 'requests',
            'rich': 'rich',
            'prompt_toolkit': 'prompt_toolkit'
        }

        all_installed = True
        for name, module in required.items():
            try:
                __import__(module)
                self.print_success(f"{name} installed")
            except ImportError:
                self.print_failure(f"{name} NOT installed")
                all_installed = False

        if not all_installed:
            print(f"\n{Colors.WARNING}Install missing dependencies:{Colors.ENDC}")
            print("  pip install -r backend/requirements-dev.txt")
            print("  pip install -r cli-requirements.txt")

        return all_installed

    def check_backend_running(self) -> bool:
        """Check if backend server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/docs", timeout=2)
            return response.status_code == 200
        except:
            return False

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None,
                   env: Optional[Dict] = None) -> tuple:
        """Run command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                env=env or os.environ.copy()
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def run_pytest(self, test_path: str, category: str,
                   marks: Optional[str] = None) -> Dict:
        """Run pytest on specific path"""
        cmd = ["python", "-m", "pytest"]

        if self.coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing"])

        if marks:
            cmd.extend(["-m", marks])

        if self.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        cmd.extend(["--tb=short", test_path])

        print(f"\n{Colors.OKBLUE}Running: {' '.join(cmd)}{Colors.ENDC}")

        returncode, stdout, stderr = self.run_command(cmd, cwd=self.backend_dir)

        # Parse output for test count
        passed = failed = skipped = 0
        for line in (stdout + stderr).split('\n'):
            if 'passed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except:
                            pass
            if 'failed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'failed' in part and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except:
                            pass

        return {
            'category': category,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'returncode': returncode,
            'output': stdout,
            'errors': stderr
        }

    def run_cli_tests(self) -> Dict:
        """Run CLI tests"""
        self.print_section("Running CLI Tests")

        # Unit tests
        print("\n📦 CLI Unit Tests (no backend required)")
        returncode, stdout, stderr = self.run_command(
            ["python", "test_cli.py"],
            cwd=self.root_dir
        )

        cli_unit_passed = returncode == 0
        if cli_unit_passed:
            self.print_success("CLI unit tests passed")
        else:
            self.print_failure("CLI unit tests failed")
            if self.verbose:
                print(stdout)
                print(stderr)

        # Integration tests (if backend running)
        backend_running = self.check_backend_running()
        cli_integration_passed = None

        if backend_running:
            print("\n🔗 CLI Integration Tests (with backend)")
            returncode, stdout, stderr = self.run_command(
                ["python", "test_cli_integration.py"],
                cwd=self.root_dir
            )
            cli_integration_passed = returncode == 0

            if cli_integration_passed:
                self.print_success("CLI integration tests passed")
            else:
                self.print_failure("CLI integration tests failed")
                if self.verbose:
                    print(stdout)
                    print(stderr)
        else:
            self.print_warning("Backend not running - CLI integration tests skipped")

        return {
            'category': 'cli',
            'unit_passed': cli_unit_passed,
            'integration_passed': cli_integration_passed,
            'backend_required': backend_running
        }

    def run_backend_tests(self, category: Optional[str] = None) -> List[Dict]:
        """Run backend tests"""
        self.print_section("Running Backend Tests")

        test_categories = {
            'infrastructure': 'tests/test_infrastructure.py',
            'phase1': 'tests/test_phase_1_infrastructure.py',
            'phase2': 'tests/test_phase_2_core_agents.py',
            'phase3': 'tests/test_phase_3_conflict_detection.py',
            'phase4': 'tests/test_phase_4_code_generation.py',
            'phase5': 'tests/test_phase_5_quality_control.py',
            'phase6': 'tests/test_phase_6_user_learning.py',
            'phase7': 'tests/test_phase_7_direct_chat.py',
            'phase8': 'tests/test_phase_8_team_collaboration.py',
            'phase9': 'tests/test_phase_9_advanced_features.py',
            'api': 'tests/test_api_projects.py',
            'integration': 'tests/test_end_to_end_integration.py',
        }

        if category and category in test_categories:
            categories_to_run = {category: test_categories[category]}
        else:
            categories_to_run = test_categories

        results = []
        for cat, test_path in categories_to_run.items():
            print(f"\n🧪 Testing: {cat}")
            result = self.run_pytest(test_path, cat)
            results.append(result)

            if result['returncode'] == 0:
                self.print_success(f"{cat}: {result['passed']} passed")
            else:
                self.print_failure(f"{cat}: {result['failed']} failed, {result['passed']} passed")

        return results

    def run_all_backend_tests(self) -> Dict:
        """Run all backend tests at once"""
        self.print_section("Running All Backend Tests")

        result = self.run_pytest("tests/", "all_backend")

        if result['returncode'] == 0:
            self.print_success(f"All tests passed: {result['passed']} tests")
        else:
            self.print_failure(f"Some tests failed: {result['failed']} failed, {result['passed']} passed")

        return result

    def generate_coverage_report(self):
        """Generate coverage report"""
        self.print_section("Generating Coverage Report")

        print("Running tests with coverage...")
        cmd = [
            "python", "-m", "pytest",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=json",
            "tests/"
        ]

        returncode, stdout, stderr = self.run_command(cmd, cwd=self.backend_dir)

        if returncode == 0:
            self.print_success("Coverage report generated")
            print("\n📊 Coverage reports:")
            print(f"  HTML: {self.backend_dir / 'htmlcov' / 'index.html'}")
            print(f"  JSON: {self.backend_dir / 'coverage.json'}")

            # Try to read coverage percentage
            coverage_json = self.backend_dir / "coverage.json"
            if coverage_json.exists():
                try:
                    with open(coverage_json) as f:
                        data = json.load(f)
                        total_coverage = data.get('totals', {}).get('percent_covered', 0)
                        print(f"\n  Total Coverage: {total_coverage:.1f}%")
                except:
                    pass
        else:
            self.print_failure("Coverage generation failed")

    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")

        duration = (self.end_time - self.start_time).total_seconds()

        print(f"Duration: {duration:.2f} seconds\n")

        # Count results
        total_passed = 0
        total_failed = 0
        total_categories = 0

        for category, result in self.results.items():
            total_categories += 1
            if isinstance(result, dict):
                if 'passed' in result:
                    total_passed += result.get('passed', 0)
                    total_failed += result.get('failed', 0)
                if 'unit_passed' in result:
                    if result['unit_passed']:
                        total_passed += 1
                    else:
                        total_failed += 1

        # Print summary table
        print(f"Categories Tested: {total_categories}")
        print(f"Tests Passed:      {Colors.OKGREEN}{total_passed}{Colors.ENDC}")
        print(f"Tests Failed:      {Colors.FAIL}{total_failed}{Colors.ENDC}")

        success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0

        print(f"\nSuccess Rate:      {Colors.BOLD}{success_rate:.1f}%{Colors.ENDC}")

        if total_failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.ENDC}")

    def run(self, fast: bool = False, category: Optional[str] = None):
        """Run test suite"""
        self.start_time = datetime.now()

        self.print_header("Socrates2 Comprehensive Test Suite")

        # Check dependencies
        if not self.check_dependencies():
            return False

        # Check backend
        backend_running = self.check_backend_running()
        if backend_running:
            self.print_success("Backend server is running at http://localhost:8000")
        else:
            self.print_warning("Backend server not running (some tests will be skipped)")
            self.print_info("Start with: cd backend && uvicorn app.main:app --reload")

        # Run tests based on options
        if fast:
            # Fast mode: only unit tests
            self.print_info("Fast mode: Running only unit tests")
            self.results['cli'] = self.run_cli_tests()
            self.results['backend_unit'] = self.run_backend_tests('infrastructure')
        elif category:
            # Specific category
            if category == 'cli':
                self.results['cli'] = self.run_cli_tests()
            else:
                self.results[category] = self.run_backend_tests(category)
        else:
            # Full suite
            self.results['cli'] = self.run_cli_tests()

            if backend_running:
                self.results['backend'] = self.run_all_backend_tests()
            else:
                # Run tests that don't need backend
                backend_results = self.run_backend_tests()
                self.results['backend'] = backend_results

        # Generate coverage if requested
        if self.coverage and backend_running:
            self.generate_coverage_report()

        self.end_time = datetime.now()

        # Print summary
        self.print_summary()

        # Return success status
        return all(
            result.get('returncode', 0) == 0 or result.get('unit_passed', False)
            for result in self.results.values()
            if isinstance(result, dict)
        )


def main():
    parser = argparse.ArgumentParser(
        description="Socrates2 Comprehensive Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests
  python run_all_tests.py --fast             # Run only fast unit tests
  python run_all_tests.py --category cli     # Run only CLI tests
  python run_all_tests.py --category phase2  # Run only Phase 2 tests
  python run_all_tests.py --coverage         # Run with coverage report
  python run_all_tests.py --verbose          # Detailed output

Test Categories:
  cli          - CLI unit and integration tests
  infrastructure - Basic infrastructure tests
  phase1-9     - Phase-specific tests
  api          - API endpoint tests
  integration  - End-to-end integration tests
        """
    )

    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run only fast unit tests'
    )

    parser.add_argument(
        '--category',
        choices=['cli', 'infrastructure', 'phase1', 'phase2', 'phase3', 'phase4',
                'phase5', 'phase6', 'phase7', 'phase8', 'phase9', 'api', 'integration'],
        help='Run specific test category'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose, coverage=args.coverage)
    success = runner.run(fast=args.fast, category=args.category)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
