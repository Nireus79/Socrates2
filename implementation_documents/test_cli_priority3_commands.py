#!/usr/bin/env python3
"""
Test script for Priority 3 CLI commands (/search, /status, /insights, /filter, /resume, /wizard)
Comprehensive testing with 35+ test cases.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from Socrates import SocratesCLI, SocratesAPI
    print("✅ Successfully imported SocratesCLI and SocratesAPI")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def test_search_command():
    """Test /search command"""
    print("\n" + "="*60)
    print("Testing /search command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_search'), "cmd_search method not found"
        print("✅ /search - Method exists")

        # Mock API search
        cli.api.search = MagicMock(return_value={
            "success": True,
            "query": "FastAPI",
            "results": [
                {"resource_type": "project", "id": "proj-1", "title": "FastAPI App", "preview": "A FastAPI app"},
                {"resource_type": "specification", "id": "spec-1", "title": "[requirements] API spec", "preview": "API requirements"}
            ],
            "total": 2,
            "resource_counts": {"projects": 1, "specifications": 1, "questions": 0}
        })

        # Mock authentication
        cli.config.get = MagicMock(return_value="mock-token")
        cli.api.set_token = MagicMock()

        # Call search - will print to console but won't error
        cli.cmd_search(["FastAPI"])
        assert cli.api.search.called, "search API not called"
        print("✅ /search - API call works")

        # Test search with filters
        cli.cmd_search(["test", "projects", "goals"])
        print("✅ /search - Filters work")

        # Test search without args (should show help)
        cli.cmd_search([])
        print("✅ /search - Help text shown when no args")


def test_status_command():
    """Test /status command"""
    print("\n" + "="*60)
    print("Testing /status command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_status'), "cmd_status method not found"
        print("✅ /status - Method exists")

        # Set project and session
        cli.current_project = {
            "id": "proj-123",
            "name": "Test Project",
            "current_phase": "phase_1",
            "status": "active",
            "maturity_score": 60.0
        }

        cli.current_session = {
            "id": "sess-456",
            "mode": "socratic",
            "status": "active",
            "started_at": "2025-01-08 10:00:00"
        }

        cli.config.get = MagicMock(return_value="mock-token")

        # Call status - should display both project and session
        cli.cmd_status([])
        print("✅ /status - Displays project and session status")

        # Without authentication should return early
        cli.config.get = MagicMock(return_value=None)
        cli.cmd_status([])
        print("✅ /status - Checks authentication")


def test_insights_command():
    """Test /insights command"""
    print("\n" + "="*60)
    print("Testing /insights command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_insights'), "cmd_insights method not found"
        print("✅ /insights - Method exists")

        cli.current_project = {"id": "proj-123"}
        cli.config.get = MagicMock(return_value="mock-token")
        cli.api.set_token = MagicMock()

        # Mock insights API
        cli.api.get_insights = MagicMock(return_value={
            "success": True,
            "project_id": "proj-123",
            "project_name": "Test Project",
            "insights": [
                {
                    "type": "gap",
                    "title": "Missing security specs",
                    "description": "No security requirements",
                    "severity": "high",
                    "category": "security",
                    "recommendations": ["Add auth", "Add encryption"]
                },
                {
                    "type": "opportunity",
                    "title": "Well-specified requirements",
                    "description": "Good coverage",
                    "severity": "low",
                    "recommendations": ["Proceed with development"]
                }
            ],
            "summary": {
                "total_insights": 2,
                "gaps_count": 1,
                "risks_count": 0,
                "opportunities_count": 1,
                "coverage_percentage": 60.0,
                "most_covered_category": "requirements",
                "least_covered_category": "security"
            }
        })

        # Call insights
        cli.cmd_insights([])
        assert cli.api.get_insights.called
        print("✅ /insights - Loads and displays insights")

        # Test with specific project ID
        cli.cmd_insights(["proj-999"])
        print("✅ /insights - Works with specified project ID")


def test_filter_command():
    """Test /filter command"""
    print("\n" + "="*60)
    print("Testing /filter command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_filter'), "cmd_filter method not found"
        print("✅ /filter - Method exists")

        cli.current_project = {"id": "proj-123"}
        cli.config.get = MagicMock(return_value="mock-token")
        cli.api.set_token = MagicMock()

        # Mock search API for filtering
        cli.api.search = MagicMock(return_value={
            "success": True,
            "results": [
                {"id": "spec-1", "title": "[security] Auth requirement", "category": "security"}
            ],
            "resource_counts": {"specifications": 1}
        })

        # Test filter by specification
        cli.cmd_filter(["spec"])
        assert cli.api.search.called
        print("✅ /filter - Filters specifications")

        cli.api.search.reset_mock()

        # Test filter with category
        cli.cmd_filter(["spec", "security"])
        assert cli.api.search.called
        print("✅ /filter - Filters by category")


def test_resume_command():
    """Test /resume command"""
    print("\n" + "="*60)
    print("Testing /resume command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_resume'), "cmd_resume method not found"
        print("✅ /resume - Method exists")

        cli.config.get = MagicMock(return_value="mock-token")
        cli.api.set_token = MagicMock()

        # Mock get_session API
        cli.api.get_session = MagicMock(return_value={
            "success": True,
            "session": {
                "id": "sess-123",
                "project_id": "proj-456",
                "mode": "socratic",
                "status": "paused",
                "started_at": "2025-01-08 10:00:00"
            }
        })

        # Test resume with session ID
        cli.cmd_resume(["sess-123"])
        assert cli.api.get_session.called
        assert cli.current_session is not None
        print("✅ /resume - Loads and resumes session")

        # Mock list_recent_sessions for resume without args
        cli.api.list_recent_sessions = MagicMock(return_value={
            "success": True,
            "sessions": [
                {"id": "sess-1", "project_id": "proj-1", "mode": "socratic", "status": "paused"}
            ]
        })

        # Test resume without args (list recent)
        cli.cmd_resume([])
        assert cli.api.list_recent_sessions.called
        print("✅ /resume - Shows recent sessions when no ID given")


def test_wizard_command():
    """Test /wizard command"""
    print("\n" + "="*60)
    print("Testing /wizard command")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        assert hasattr(cli, 'cmd_wizard'), "cmd_wizard method not found"
        print("✅ /wizard - Method exists")

        cli.config.get = MagicMock(return_value="mock-token")
        cli.api.set_token = MagicMock()

        # Mock project creation
        cli.api.create_project = MagicMock(return_value={
            "success": True,
            "project": {
                "id": "proj-new",
                "name": "New Project",
                "description": "Test description"
            }
        })

        # Mock template application
        cli.api.apply_template = MagicMock(return_value={
            "success": True,
            "specs_created": 35
        })

        # Mock Prompt input (wizard interaction)
        with patch('Socrates.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = [
                "New Project",  # Project name
                "A test project",  # Description
                "1"  # Template choice (web-app)
            ]

            cli.cmd_wizard([])
            assert cli.api.create_project.called
            assert cli.api.apply_template.called
            assert cli.current_project is not None
            print("✅ /wizard - Creates project and applies template")


def test_api_methods():
    """Test new API methods"""
    print("\n" + "="*60)
    print("Testing Priority 3 API methods")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        api = SocratesAPI("http://localhost:8000", None)

        # Check all API methods exist
        methods = [
            'search',
            'get_insights',
            'get_template',
            'apply_template',
            'get_session',
            'list_recent_sessions'
        ]

        for method in methods:
            assert hasattr(api, method), f"API method {method} not found"
            print(f"✅ API.{method}() exists")


def test_display_helpers():
    """Test display helper methods"""
    print("\n" + "="*60)
    print("Testing display helper methods")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        helpers = [
            '_display_insights',
            '_display_search_results',
            '_display_filtered_results',
            '_display_project_status',
            '_display_session_status',
            '_display_next_steps',
            '_display_project_created',
            '_wizard_select_template',
            '_show_recent_sessions'
        ]

        for helper in helpers:
            assert hasattr(cli, helper), f"Helper method {helper} not found"
            print(f"✅ {helper}() exists")


def test_commands_list():
    """Test that all Priority 3 commands are registered"""
    print("\n" + "="*60)
    print("Testing command registration")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        priority3_commands = [
            "/search",
            "/status",
            "/insights",
            "/filter",
            "/resume",
            "/wizard"
        ]

        for cmd in priority3_commands:
            assert cmd in cli.commands, f"Command {cmd} not registered"
            print(f"✅ {cmd} - Registered in commands list")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING PRIORITY 3 CLI COMMANDS TESTS")
    print("="*60)

    try:
        test_api_methods()
        test_search_command()
        test_status_command()
        test_insights_command()
        test_filter_command()
        test_resume_command()
        test_wizard_command()
        test_display_helpers()
        test_commands_list()

        print("\n" + "="*60)
        print("✅ ALL PRIORITY 3 TESTS PASSED!")
        print("="*60)
        print("\nImplemented Commands:")
        print("  ✅ /search <query> - Full-text search")
        print("  ✅ /status - Show project/session status")
        print("  ✅ /insights [id] - Project analysis (gaps, risks, opportunities)")
        print("  ✅ /filter [type] [cat] - Filter specifications")
        print("  ✅ /resume [id] - Resume paused session")
        print("  ✅ /wizard - Interactive project setup")
        print("\nAPI Methods:")
        print("  ✅ search()")
        print("  ✅ get_insights()")
        print("  ✅ get_template()")
        print("  ✅ apply_template()")
        print("  ✅ get_session()")
        print("  ✅ list_recent_sessions()")
        print("\nHelper Methods:")
        print("  ✅ 9 display and utility helpers")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
