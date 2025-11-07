#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Socrates2 CLI - Command-line interface for the Socrates2 AI-Powered Specification Assistant

This CLI provides commands to:
- Start the FastAPI server
- Run migrations
- Run tests
- Check project health
- View registered agents and endpoints
"""

import click
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


@click.group()
@click.version_option(version="0.1.0", prog_name="Socrates2")
def cli():
    """Socrates2 - AI-Powered Specification Assistant CLI"""
    pass


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Server host address",
    show_default=True
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Server port",
    show_default=True
)
@click.option(
    "--reload",
    is_flag=True,
    default=True,
    help="Enable auto-reload on code changes",
)
@click.option(
    "--no-reload",
    is_flag=True,
    help="Disable auto-reload"
)
def run(host: str, port: int, reload: bool, no_reload: bool):
    """Start the Socrates2 API server"""
    if no_reload:
        reload = False

    click.echo("[*] Starting Socrates2 API Server...")
    click.echo("[*] Host: {}".format(host))
    click.echo("[*] Port: {}".format(port))
    click.echo("[*] Auto-reload: {}".format("Enabled" if reload else "Disabled"))
    click.echo("[*] API Docs: http://{}:{}/docs".format(host, port))
    click.echo()

    os.chdir(BACKEND_DIR)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host={}".format(host),
        "--port={}".format(port),
    ]

    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\n[!] Server stopped")
    except subprocess.CalledProcessError as e:
        click.echo("[ERROR] Error starting server: {}".format(e), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output"
)
@click.option(
    "--coverage",
    is_flag=True,
    help="Run with coverage report"
)
@click.option(
    "--failfast",
    "-x",
    is_flag=True,
    help="Stop on first failure"
)
def test(verbose: bool, coverage: bool, failfast: bool):
    """Run test suite"""
    click.echo("[*] Running test suite...")
    click.echo()

    os.chdir(BACKEND_DIR)

    cmd = [sys.executable, "-m", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html"])

    if failfast:
        cmd.append("-x")

    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        click.echo("\n[!] Tests stopped")
        sys.exit(130)


@cli.command()
@click.option(
    "--phase",
    type=int,
    help="Run tests for specific phase (e.g., --phase 7)"
)
def test_phase(phase: Optional[int]):
    """Run phase-specific tests"""
    os.chdir(BACKEND_DIR)

    if phase:
        test_file = "tests/test_phase_{}_*.py".format(phase)
        click.echo("[*] Running Phase {} tests...".format(phase))
    else:
        click.echo("[*] Running all phase tests...")
        test_file = "tests/test_phase_*.py"

    cmd = [sys.executable, "-m", "pytest", test_file, "-v"]

    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        click.echo("\n[!] Tests stopped")
        sys.exit(130)


@cli.command()
def migrate():
    """Run database migrations"""
    click.echo("[*] Running database migrations...")
    click.echo()

    os.chdir(BACKEND_DIR)

    # Check for .env file
    if not (BACKEND_DIR / ".env").exists():
        click.echo("[ERROR] .env file not found in backend directory", err=True)
        click.echo("[*] Run 'python setup_env.py' first", err=True)
        sys.exit(1)

    cmd = [sys.executable, "scripts/run_migrations.ps1"]

    try:
        if sys.platform == "win32":
            # On Windows, use PowerShell
            click.echo("[*] Using PowerShell to run migrations...")
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(BACKEND_DIR / "scripts/run_migrations.ps1")],
                check=True
            )
        else:
            # On other platforms, use bash
            click.echo("[*] Using bash to run migrations...")
            subprocess.run(
                ["bash", str(BACKEND_DIR / "scripts/run_migrations.ps1")],
                check=True
            )
        click.echo("[OK] Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        click.echo("[ERROR] Migration failed: {}".format(e), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n[!] Migration stopped")
        sys.exit(130)


@cli.command()
def health():
    """Check Socrates2 API health and database connections"""
    click.echo("[*] Checking Socrates2 health...")
    click.echo()

    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))

    try:
        from backend.app.core.config import settings
        from backend.app.core.database import get_db_auth, get_db_specs

        # Check configuration
        click.echo("[*] Configuration:")
        click.echo("[*] Environment: {}".format(settings.ENVIRONMENT))
        click.echo("[*] Debug Mode: {}".format(settings.DEBUG))
        click.echo("[*] Log Level: {}".format(settings.LOG_LEVEL))
        click.echo()

        # Check database connections
        click.echo("[*] Database Connections:")

        try:
            auth_db = get_db_auth()
            click.echo("[OK] socrates_auth: Connected")
        except Exception as e:
            click.echo("[ERROR] socrates_auth: {}".format(str(e)), err=True)

        try:
            specs_db = get_db_specs()
            click.echo("[OK] socrates_specs: Connected")
        except Exception as e:
            click.echo("[ERROR] socrates_specs: {}".format(str(e)), err=True)

        click.echo()
        click.echo("[OK] Health check complete")
        click.echo()
        click.echo("[*] To start the server, run: python Socrates.py run")

    except Exception as e:
        click.echo("[ERROR] Health check failed: {}".format(e), err=True)
        sys.exit(1)


@cli.command()
def info():
    """Display Socrates2 project information"""
    click.echo()
    click.echo("=" * 62)
    click.echo("  Socrates2 - AI-Powered Specification Assistant")
    click.echo("=" * 62)
    click.echo()

    click.echo("[*] Project Information:")
    click.echo("    Version: 0.1.0")
    click.echo("    Phase: Phase 1 - Infrastructure + Phases 2-9")
    click.echo("    Status: Active Development")
    click.echo()

    click.echo("[*] Architecture:")
    click.echo("    * Database 1: socrates_auth (authentication & users)")
    click.echo("    * Database 2: socrates_specs (projects, specs, conversations)")
    click.echo("    * Framework: FastAPI with async support")
    click.echo("    * Migration Tool: Alembic (19 migrations)")
    click.echo()

    click.echo("[*] Registered Agents:")
    agents = [
        "Project Manager",
        "Socratic Counselor",
        "Context Analyzer",
        "Conflict Detector",
        "Code Generator",
        "Quality Controller",
        "User Learning",
        "Direct Chat",
        "Team Collaboration",
        "Export Agent",
        "Multi-LLM Manager",
        "GitHub Integration",
    ]
    for agent in agents:
        click.echo("    * {}".format(agent))
    click.echo()

    click.echo("[*] Available Phases:")
    phases = [
        ("Phase 1", "Infrastructure (users, projects, sessions)"),
        ("Phase 2", "Core Agents (project manager, socratic counselor)"),
        ("Phase 3", "Conflict Detection"),
        ("Phase 4", "Code Generation"),
        ("Phase 5", "Quality Control"),
        ("Phase 6", "User Learning & Knowledge Base"),
        ("Phase 7", "Direct Chat Mode"),
        ("Phase 8", "Team Collaboration"),
        ("Phase 9", "Multi-LLM & Integrations"),
    ]
    for phase, desc in phases:
        click.echo("    [OK] {}: {}".format(phase, desc))
    click.echo()

    click.echo("[*] Project Location:")
    click.echo("    {}".format(PROJECT_ROOT))
    click.echo()

    click.echo("[*] API Documentation:")
    click.echo("    http://localhost:8000/docs (when server is running)")
    click.echo()


@cli.command()
@click.option(
    "--web",
    is_flag=True,
    help="Open API docs in browser"
)
def docs(web: bool):
    """Show API documentation links and information"""
    click.echo()
    click.echo("Socrates2 API Documentation")
    click.echo("=" * 50)
    click.echo()

    click.echo("[*] Make sure the server is running:")
    click.echo("    python Socrates.py run")
    click.echo()

    click.echo("[*] Documentation URLs:")
    click.echo("    * Interactive Docs (Swagger UI):")
    click.echo("      http://localhost:8000/docs")
    click.echo()
    click.echo("    * Alternative Docs (ReDoc):")
    click.echo("      http://localhost:8000/redoc")
    click.echo()
    click.echo("    * OpenAPI Schema (JSON):")
    click.echo("      http://localhost:8000/openapi.json")
    click.echo()

    click.echo("[*] API Endpoints:")
    click.echo("    * Root: GET /")
    click.echo("    * API Info: GET /api/v1/info")
    click.echo("    * Health: GET /api/v1/admin/health")
    click.echo()
    click.echo("[*] Auth Endpoints:")
    click.echo("    * Register: POST /api/v1/auth/register")
    click.echo("    * Login: POST /api/v1/auth/login")
    click.echo("    * Logout: POST /api/v1/auth/logout")
    click.echo()

    if web:
        click.echo("[*] Opening API docs in browser...")
        import webbrowser
        webbrowser.open("http://localhost:8000/docs")


@cli.command()
def setup():
    """Setup project environment and dependencies"""
    click.echo("[*] Setting up Socrates2 project...")
    click.echo()

    os.chdir(BACKEND_DIR)

    # Check if .env exists
    if not (BACKEND_DIR / ".env").exists():
        click.echo("[*] Creating .env file...")
        try:
            subprocess.run(
                [sys.executable, "scripts/setup_env.py"],
                check=True
            )
            click.echo("[OK] .env file created")
        except subprocess.CalledProcessError:
            click.echo("[ERROR] Failed to create .env file", err=True)
            sys.exit(1)
    else:
        click.echo("[OK] .env file already exists")

    click.echo()
    click.echo("[*] Verifying dependencies...")
    try:
        subprocess.run(
            [sys.executable, "scripts/verify_dependencies.py"],
            check=True
        )
        click.echo("[OK] All dependencies verified")
    except subprocess.CalledProcessError:
        click.echo("[ERROR] Some dependencies are missing", err=True)
        sys.exit(1)

    click.echo()
    click.echo("[OK] Setup complete!")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Run migrations: python Socrates.py migrate")
    click.echo("  2. Check health:  python Socrates.py health")
    click.echo("  3. Start server:  python Socrates.py run")


@cli.command()
def status():
    """Show project status and git information"""
    click.echo()
    click.echo("Socrates2 Project Status")
    click.echo("=" * 50)
    click.echo()

    # Git status
    try:
        os.chdir(PROJECT_ROOT)
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("[*] Git Status:")
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    click.echo("    {}".format(line))
            else:
                click.echo("    Working directory clean [OK]")
            click.echo()
    except Exception as e:
        click.echo("    Could not get git status: {}".format(e))

    # Branch info
    try:
        result = subprocess.run(
            ["git", "branch", "-v"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("[*] Branches:")
            for line in result.stdout.strip().split('\n'):
                click.echo("    {}".format(line))
            click.echo()
    except Exception:
        pass

    # Test status
    click.echo("[*] Test Status:")
    os.chdir(BACKEND_DIR)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--co", "-q"],
            capture_output=True,
            text=True,
            timeout=10
        )
        test_count = len([line for line in result.stdout.split('\n') if line.strip() and not line.startswith(' ')])
        click.echo("    Total tests found: {}".format(test_count))
        click.echo()
    except Exception:
        pass

    click.echo("[*] Directories:")
    click.echo("    Project: {}".format(PROJECT_ROOT))
    click.echo("    Backend: {}".format(BACKEND_DIR))
    click.echo("    Tests: {}".format(BACKEND_DIR / 'tests'))
    click.echo("    Migrations: {}".format(BACKEND_DIR / 'alembic' / 'versions'))
    click.echo()


if __name__ == "__main__":
    cli()
