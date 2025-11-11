"""Main CLI entry point for Socrates2.

Provides command-line interface for project management, specification handling,
and configuration management.
"""
import click
import sys
import os
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .commands import projects, specifications, config, auth


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="socrates")
@click.pass_context
def main(ctx):
    """
    Socrates2 - AI-Powered Specification Assistant CLI

    Manage projects, specifications, and configurations from the command line.

    Examples:
        socrates --version
        socrates --help
        socrates project create --name "My Project"
        socrates spec list --project PROJECT_ID
        socrates export --project PROJECT_ID --format csv
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add command groups
main.add_command(projects.project)
main.add_command(specifications.spec)
main.add_command(auth.auth)
main.add_command(config.config)


if __name__ == "__main__":
    main()
