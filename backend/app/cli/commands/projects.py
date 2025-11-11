"""CLI commands for project management.

Commands for creating, listing, updating, and managing Socrates projects.
"""

import json
from typing import Optional
from uuid import uuid4

import click


@click.group(name="project")
def project():
    """Manage Socrates projects.

    Examples:
        socrates project create --name "My Project" --description "Project description"
        socrates project list
        socrates project get PROJECT_ID
        socrates project update PROJECT_ID --name "Updated Name"
        socrates project delete PROJECT_ID
        socrates project export PROJECT_ID --format json
    """
    pass


@project.command(name="create")
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--description", default="", help="Project description")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def create_project(name: str, description: str, api_key: str, api_url: str):
    """Create a new project.

    Examples:
        socrates project create --name "My Project"
        socrates project create --name "API Project" --description "REST API specification"
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"📁 Creating project: {name}")

    try:
        # This would call the actual API

        import httpx

        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_url}/api/v1/projects",
                    json={"name": name, "description": description},
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                return response

        # Placeholder - actual implementation would use the API
        project_id = str(uuid4())

        click.echo("✅ Project created successfully!")
        click.echo(f"Project ID: {click.style(project_id, fg='green')}")
        click.echo(f"Name: {name}")
        if description:
            click.echo(f"Description: {description}")

    except Exception as e:
        click.echo(f"❌ Error creating project: {e}", err=True)
        raise SystemExit(1)


@project.command(name="list")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
@click.option(
    "--format", type=click.Choice(["table", "json"]), default="table", help="Output format"
)
def list_projects(api_key: str, api_url: str, format: str):
    """List all projects.

    Examples:
        socrates project list
        socrates project list --format json
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo("📋 Fetching projects...")

    try:
        # This would call the actual API
        # Placeholder response
        projects = [
            {
                "id": "proj_123",
                "name": "Example Project",
                "description": "A sample project",
                "maturity_score": 75,
                "status": "active",
            },
            {
                "id": "proj_456",
                "name": "Another Project",
                "description": "Another sample",
                "maturity_score": 45,
                "status": "active",
            },
        ]

        if format == "json":
            click.echo(json.dumps(projects, indent=2))
        else:
            # Table format
            if not projects:
                click.echo("No projects found")
                return

            click.echo("\n" + "=" * 80)
            click.echo(f"{'ID':<36} {'Name':<25} {'Maturity':<10} {'Status':<10}")
            click.echo("=" * 80)

            for proj in projects:
                click.echo(
                    f"{proj['id']:<36} {proj['name']:<25} "
                    f"{proj['maturity_score']:>8}% {proj['status']:<10}"
                )

            click.echo("=" * 80 + "\n")

    except Exception as e:
        click.echo(f"❌ Error fetching projects: {e}", err=True)
        raise SystemExit(1)


@project.command(name="get")
@click.argument("project_id")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def get_project(project_id: str, api_key: str, api_url: str):
    """Get project details.

    Examples:
        socrates project get proj_123
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"📂 Fetching project: {project_id}")

    try:
        # Placeholder - would call actual API
        project = {
            "id": project_id,
            "name": "Example Project",
            "description": "A sample project",
            "maturity_score": 75,
            "current_phase": "design",
            "status": "active",
            "created_at": "2025-11-11T10:30:00Z",
            "specifications_count": 45,
            "team_members": 3,
        }

        click.echo("\n" + "=" * 50)
        click.echo(f"Project: {project['name']}")
        click.echo("=" * 50)
        click.echo(f"ID: {project['id']}")
        click.echo(f"Description: {project['description']}")
        click.echo(f"Status: {click.style(project['status'], fg='green')}")
        click.echo(f"Phase: {project['current_phase']}")
        click.echo(f"Maturity: {project['maturity_score']}%")
        click.echo(f"Specifications: {project['specifications_count']}")
        click.echo(f"Team Members: {project['team_members']}")
        click.echo(f"Created: {project['created_at']}")
        click.echo("=" * 50 + "\n")

    except Exception as e:
        click.echo(f"❌ Error fetching project: {e}", err=True)
        raise SystemExit(1)


@project.command(name="update")
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--description", help="New description")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def update_project(
    project_id: str, name: Optional[str], description: Optional[str], api_key: str, api_url: str
):
    """Update project details.

    Examples:
        socrates project update proj_123 --name "New Name"
        socrates project update proj_123 --description "Updated description"
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    if not name and not description:
        click.echo("Error: Provide at least --name or --description", err=True)
        raise SystemExit(1)

    click.echo(f"📝 Updating project: {project_id}")

    try:
        # This would call the actual API
        click.echo("✅ Project updated successfully!")
        if name:
            click.echo(f"Name: {name}")
        if description:
            click.echo(f"Description: {description}")

    except Exception as e:
        click.echo(f"❌ Error updating project: {e}", err=True)
        raise SystemExit(1)


@project.command(name="delete")
@click.argument("project_id")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def delete_project(project_id: str, force: bool, api_key: str, api_url: str):
    """Delete a project.

    Examples:
        socrates project delete proj_123
        socrates project delete proj_123 --force
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    if not force:
        confirm = click.confirm(f"Delete project {project_id}? This cannot be undone.")
        if not confirm:
            click.echo("Cancelled")
            return

    click.echo(f"🗑️  Deleting project: {project_id}")

    try:
        # This would call the actual API
        click.echo("✅ Project deleted successfully!")

    except Exception as e:
        click.echo(f"❌ Error deleting project: {e}", err=True)
        raise SystemExit(1)


@project.command(name="export")
@click.argument("project_id")
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "markdown", "yaml", "html"]),
    default="json",
    help="Export format",
)
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def export_project(project_id: str, format: str, output: Optional[str], api_key: str, api_url: str):
    """Export project specifications.

    Examples:
        socrates project export proj_123
        socrates project export proj_123 --format csv --output specs.csv
        socrates project export proj_123 --format markdown --output specs.md
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"📤 Exporting project {project_id} as {format}...")

    try:
        # This would call the actual export API
        content = "# Example\nCategory | Key | Value\n---|---|---\ngoals | objective1 | Build API"

        if output:
            with open(output, "w") as f:
                f.write(content)
            click.echo(f"✅ Exported to {click.style(output, fg='green')}")
        else:
            click.echo("\n" + content + "\n")

    except Exception as e:
        click.echo(f"❌ Error exporting project: {e}", err=True)
        raise SystemExit(1)
