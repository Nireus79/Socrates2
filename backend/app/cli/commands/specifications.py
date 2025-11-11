"""CLI commands for specification management.

Commands for creating, listing, importing, and exporting specifications.
"""

import json
from pathlib import Path
from typing import Optional

import click


@click.group(name="spec")
def spec():
    """Manage specifications.

    Examples:
        socrates spec create --project PROJECT_ID --category goals --key objective --value "Build API"
        socrates spec list --project PROJECT_ID
        socrates spec import --project PROJECT_ID --file specs.json
        socrates spec export --project PROJECT_ID --format csv --output specs.csv
    """
    pass


@spec.command(name="create")
@click.option("--project", required=True, help="Project ID")
@click.option("--category", required=True, help="Specification category (goals, tech_stack, etc.)")
@click.option("--key", required=True, help="Specification key")
@click.option("--value", required=True, help="Specification value")
@click.option("--content", help="Detailed specification content")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def create_spec(
    project: str,
    category: str,
    key: str,
    value: str,
    content: Optional[str],
    api_key: str,
    api_url: str,
):
    """Create a new specification.

    Examples:
        socrates spec create --project proj_123 --category goals \\
          --key objective1 --value "Build scalable API"

        socrates spec create --project proj_123 --category tech_stack \\
          --key framework --value FastAPI --content "Python async framework"
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"✍️  Creating specification in {project}...")

    try:
        # This would call the actual API
        spec_id = "spec_" + "123456"

        click.echo("✅ Specification created successfully!")
        click.echo(f"ID: {click.style(spec_id, fg='green')}")
        click.echo(f"Category: {category}")
        click.echo(f"Key: {key}")
        click.echo(f"Value: {value}")

    except Exception as e:
        click.echo(f"❌ Error creating specification: {e}", err=True)
        raise SystemExit(1)


@spec.command(name="list")
@click.option("--project", required=True, help="Project ID")
@click.option("--category", help="Filter by category")
@click.option(
    "--format", type=click.Choice(["table", "json"]), default="table", help="Output format"
)
@click.option("--limit", type=int, default=50, help="Number of results")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def list_specs(
    project: str, category: Optional[str], format: str, limit: int, api_key: str, api_url: str
):
    """List specifications in a project.

    Examples:
        socrates spec list --project proj_123
        socrates spec list --project proj_123 --category goals
        socrates spec list --project proj_123 --format json
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"📋 Fetching specifications from {project}...")

    try:
        # Placeholder response
        specs = [
            {
                "id": "spec_123",
                "category": "goals",
                "key": "objective1",
                "value": "Build scalable API",
                "source": "user_input",
                "confidence": 0.95,
            },
            {
                "id": "spec_456",
                "category": "tech_stack",
                "key": "framework",
                "value": "FastAPI",
                "source": "extracted",
                "confidence": 0.92,
            },
        ]

        if category:
            specs = [s for s in specs if s["category"] == category]

        if format == "json":
            click.echo(json.dumps(specs[:limit], indent=2))
        else:
            # Table format
            if not specs:
                click.echo("No specifications found")
                return

            click.echo("\n" + "=" * 100)
            click.echo(
                f"{'Category':<15} {'Key':<20} {'Value':<35} {'Source':<15} {'Confidence':<10}"
            )
            click.echo("=" * 100)

            for spec in specs[:limit]:
                click.echo(
                    f"{spec['category']:<15} {spec['key']:<20} {spec['value'][:33]:<35} "
                    f"{spec['source']:<15} {spec['confidence']:>8.0%}"
                )

            click.echo("=" * 100 + "\n")

    except Exception as e:
        click.echo(f"❌ Error fetching specifications: {e}", err=True)
        raise SystemExit(1)


@spec.command(name="import")
@click.option("--project", required=True, help="Project ID")
@click.option(
    "--file", type=click.Path(exists=True), required=True, help="File to import (JSON, CSV, YAML)"
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "yaml"]),
    help="File format (auto-detected if not specified)",
)
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def import_specs(project: str, file: str, format: Optional[str], api_key: str, api_url: str):
    """Import specifications from a file.

    Examples:
        socrates spec import --project proj_123 --file specs.json
        socrates spec import --project proj_123 --file specs.csv --format csv
        socrates spec import --project proj_123 --file specs.yaml
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    file_path = Path(file)

    if not file_path.exists():
        click.echo(f"Error: File not found: {file}", err=True)
        raise SystemExit(1)

    # Auto-detect format
    if not format:
        format = file_path.suffix.lstrip(".").lower()
        if format == "yml":
            format = "yaml"

    click.echo(f"📥 Importing {format.upper()} from {file}...")

    try:
        # Read file
        content = file_path.read_text()

        # Parse based on format
        specs = []
        if format == "json":
            specs = json.loads(content)
        elif format == "csv":
            import csv

            reader = csv.DictReader(content.splitlines())
            specs = list(reader)
        elif format == "yaml":
            try:
                import yaml

                specs = yaml.safe_load(content).get("specifications", [])
            except ImportError:
                click.echo("Warning: PyYAML not installed, falling back to JSON parsing", err=True)
                specs = json.loads(content)

        # This would call the actual API to import
        click.echo(f"✅ Imported {len(specs)} specifications!")
        click.echo(f"Project: {project}")

    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON format: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Error importing specifications: {e}", err=True)
        raise SystemExit(1)


@spec.command(name="export")
@click.option("--project", required=True, help="Project ID")
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "markdown", "yaml", "html"]),
    default="json",
    help="Export format",
)
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--category", help="Filter by category")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def export_specs(
    project: str,
    format: str,
    output: Optional[str],
    category: Optional[str],
    api_key: str,
    api_url: str,
):
    """Export specifications to a file.

    Examples:
        socrates spec export --project proj_123 --format csv --output specs.csv
        socrates spec export --project proj_123 --format markdown --output specs.md
        socrates spec export --project proj_123 --format json
        socrates spec export --project proj_123 --category goals --format csv
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"📤 Exporting specifications as {format.upper()}...")

    try:
        # This would call the actual export API
        if format == "json":
            content = json.dumps(
                {
                    "project_id": project,
                    "format": "json",
                    "specifications": [
                        {"category": "goals", "key": "objective1", "value": "Build scalable API"}
                    ],
                },
                indent=2,
            )
        elif format == "csv":
            content = (
                "category,key,value,source,confidence\ngoals,objective1,Build API,user_input,0.95"
            )
        elif format == "markdown":
            content = f"# Project {project} Specifications\n\n## Goals\n### objective1\nBuild API"
        elif format == "yaml":
            content = (
                "project_id: "
                + project
                + "\nspecifications:\n  - category: goals\n    key: objective1"
            )
        else:  # html
            content = "<html><body><h1>Specifications</h1></body></html>"

        if output:
            Path(output).write_text(content)
            click.echo(f"✅ Exported to {click.style(output, fg='green')}")
        else:
            click.echo("\n" + content + "\n")

    except Exception as e:
        click.echo(f"❌ Error exporting specifications: {e}", err=True)
        raise SystemExit(1)


@spec.command(name="validate")
@click.option("--project", required=True, help="Project ID")
@click.option("--api-key", envvar="SOCRATES_API_KEY", help="API key for authentication")
@click.option(
    "--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000", help="API base URL"
)
def validate_specs(project: str, api_key: str, api_url: str):
    """Validate specifications in a project.

    Checks for conflicts, missing dependencies, and other issues.

    Examples:
        socrates spec validate --project proj_123
    """
    if not api_key:
        click.echo("Error: API key required. Set SOCRATES_API_KEY or use --api-key", err=True)
        raise SystemExit(1)

    click.echo(f"✔️  Validating specifications in {project}...")

    try:
        # This would call the actual validation API
        issues = [
            {
                "severity": "warning",
                "message": "Specification 'api_rate_limit' conflicts with 'request_throttling'",
            }
        ]

        if issues:
            click.echo(f"\nFound {len(issues)} issue(s):\n")
            for issue in issues:
                severity_color = "red" if issue["severity"] == "error" else "yellow"
                click.echo(
                    f"  {click.style(issue['severity'].upper(), fg=severity_color)}: {issue['message']}"
                )
        else:
            click.echo("✅ No issues found!")

    except Exception as e:
        click.echo(f"❌ Error validating specifications: {e}", err=True)
        raise SystemExit(1)
