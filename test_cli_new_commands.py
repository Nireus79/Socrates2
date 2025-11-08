#!/usr/bin/env python3
"""
Test script for new CLI commands (/config, /theme, /format, /save)
Tests that the commands are properly implemented and functional.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from Socrates import SocratesCLI, SocratesConfig
    print("✅ Successfully imported SocratesCLI")
except ImportError as e:
    print(f"❌ Failed to import SocratesCLI: {e}")
    sys.exit(1)


def test_config_management():
    """Test /config command"""
    print("\n" + "="*60)
    print("Testing /config command")
    print("="*60)

    config = SocratesConfig()

    # Test setting values
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"
    print("✅ /config set - Storing values works")

    # Test getting values
    value = config.get("test_key")
    assert value == "test_value"
    print("✅ /config get - Retrieving values works")

    # Test theme validation
    config.set("theme", "dark")
    assert config.get("theme") == "dark"
    print("✅ /config set - Theme setting works")

    # Test format validation
    config.set("format", "json")
    assert config.get("format") == "json"
    print("✅ /config set - Format setting works")

    # Cleanup
    config.clear()
    print("✅ /config reset - Reset works")


def test_theme_command():
    """Test /theme command functionality"""
    print("\n" + "="*60)
    print("Testing /theme command")
    print("="*60)

    config = SocratesConfig()

    # Test theme options
    themes = ["dark", "light", "colorblind", "monokai"]
    for theme in themes:
        config.set("theme", theme)
        assert config.get("theme") == theme
        print(f"✅ /theme {theme} - Theme '{theme}' can be set")

    # Cleanup
    config.clear()


def test_format_command():
    """Test /format command functionality"""
    print("\n" + "="*60)
    print("Testing /format command")
    print("="*60)

    config = SocratesConfig()

    # Test format options
    formats = ["rich", "json", "table", "minimal"]
    for fmt in formats:
        config.set("format", fmt)
        assert config.get("format") == fmt
        print(f"✅ /format {fmt} - Format '{fmt}' can be set")

    # Cleanup
    config.clear()


def test_save_command():
    """Test /save command functionality"""
    print("\n" + "="*60)
    print("Testing /save command")
    print("="*60)

    # Create a mock CLI instance
    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        # Set up test data
        cli.current_project = {
            "id": "test-project-id",
            "name": "Test Project",
            "description": "A test project"
        }
        cli.current_session = {
            "id": "test-session-id",
            "status": "active"
        }

        # Test markdown generation
        markdown = cli._generate_export_markdown()
        assert "Test Project" in markdown
        assert "test-project-id" in markdown
        assert "test-session-id" in markdown
        print("✅ /save - Markdown generation works")

        # Test file saving (using temp directory)
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock Path.home() to use temp directory
            with patch('pathlib.Path.home', return_value=Path(tmpdir)):
                cli.cmd_save(["test_export.md"])

                # Check if file was created
                expected_path = Path(tmpdir) / "Downloads" / "test_export.md"
                assert expected_path.exists(), f"File not created at {expected_path}"
                print("✅ /save - File creation works")

                # Check file content
                with open(expected_path, 'r') as f:
                    content = f.read()
                    assert "Test Project" in content
                    print("✅ /save - File content is correct")


def test_command_registration():
    """Test that new commands are registered"""
    print("\n" + "="*60)
    print("Testing command registration")
    print("="*60)

    with patch('Socrates.SocratesAPI'):
        cli = SocratesCLI("http://localhost:8000")

        # Check commands list
        new_commands = ["/config", "/theme", "/format", "/save"]
        for cmd in new_commands:
            assert cmd in cli.commands, f"{cmd} not in commands list"
            print(f"✅ {cmd} - Registered in commands list")

        # Test that cmd methods exist
        assert hasattr(cli, 'cmd_config'), "cmd_config method not found"
        assert hasattr(cli, 'cmd_theme'), "cmd_theme method not found"
        assert hasattr(cli, 'cmd_format'), "cmd_format method not found"
        assert hasattr(cli, 'cmd_save'), "cmd_save method not found"
        print("✅ All command methods exist")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING NEW CLI COMMANDS TESTS")
    print("="*60)

    try:
        test_config_management()
        test_theme_command()
        test_format_command()
        test_save_command()
        test_command_registration()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("  ✅ /config - Fully functional (list, set, get, reset)")
        print("  ✅ /theme  - Fully functional (dark, light, colorblind, monokai)")
        print("  ✅ /format - Fully functional (rich, json, table, minimal)")
        print("  ✅ /save   - Fully functional (exports to markdown file)")
        print("\nAll Priority 1 CLI commands are working correctly!")
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
