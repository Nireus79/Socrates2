"""
Socrates CLI - Command line interface for managing domains and specifications.

Provides commands for:
- Listing and exploring domains
- Creating and managing workflows
- Validating specifications
- Exporting specifications in various formats
- Viewing analytics and metrics
"""

import json

import click

from ..domains import get_domain_registry
from ..domains.analytics import get_domain_analytics
from ..domains.registry import register_all_domains
from ..domains.workflows import get_workflow_manager

# Ensure domains are registered
try:
    register_all_domains()
except ValueError:
    # Domains already registered
    pass


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="socrates")
@click.pass_context
def cli(ctx):
    """
    Socrates - AI-Powered Specification Assistant CLI.

    Commands for working with knowledge domains and specifications.
    """
    if ctx.invoked_subcommand is None:
        click.echo("Socrates CLI v0.1.0")
        click.echo("Use 'socrates --help' to see available commands")


@cli.group()
def domain():
    """Domain management commands."""
    pass


@domain.command()
def list():
    """List all available domains."""
    registry = get_domain_registry()
    domains = registry.list_domains()

    if not domains:
        click.echo("No domains registered")
        return

    click.secho("\nAvailable Domains:", fg="cyan", bold=True)
    for domain_id, domain in domains.items():
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()

        click.echo(f"\n  {domain.name} ({domain_id})")
        click.echo(f"    Version: {domain.version}")
        click.echo(
            f"    Questions: {len(questions)}, Exporters: {len(exporters)}, Rules: {len(rules)}"
        )

    click.echo(f"\nTotal: {len(domains)} domains")


@domain.command()
@click.argument("domain_id")
def info(domain_id: str):
    """Get detailed information about a domain."""
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        click.secho(f"Error: Domain '{domain_id}' not found", fg="red")
        available = ", ".join(registry.list_domain_ids())
        click.echo(f"Available domains: {available}")
        return

    domain = registry.get_domain(domain_id)

    click.secho(f"\n{domain.name} ({domain_id})", fg="cyan", bold=True)
    click.echo(f"Version: {domain.version}")
    click.echo(f"Description: {domain.description}")
    click.echo(f"Categories: {', '.join(domain.get_categories())}")

    questions = domain.get_questions()
    exporters = domain.get_export_formats()
    rules = domain.get_conflict_rules()
    analyzers = domain.get_quality_analyzers()

    click.echo(f"\nQuestions: {len(questions)}")
    click.echo(f"Export Formats: {len(exporters)}")
    click.echo(f"Conflict Rules: {len(rules)}")
    click.echo(f"Quality Analyzers: {len(analyzers)}")

    if exporters:
        click.echo("\nExport Formats:")
        for e in exporters:
            click.echo(f"  • {e.format_id}: {e.name} ({e.file_extension})")


@domain.command()
@click.argument("domain_id")
def questions(domain_id: str):
    """List all questions for a domain."""
    registry = get_domain_registry()

    if not registry.has_domain(domain_id):
        click.secho(f"Error: Domain '{domain_id}' not found", fg="red")
        return

    domain = registry.get_domain(domain_id)
    questions = domain.get_questions()

    click.secho(f"\n{domain.name} - Questions", fg="cyan", bold=True)
    click.echo(f"Total: {len(questions)}\n")

    for i, q in enumerate(questions, 1):
        click.secho(f"{i}. {q.question_id}", fg="green", bold=True)
        click.echo(f"   Text: {q.text}")
        click.echo(f"   Category: {q.category}")
        click.echo(f"   Difficulty: {q.difficulty}")
        if q.help_text:
            click.echo(f"   Help: {q.help_text}")
        click.echo()


@cli.group()
def workflow():
    """Workflow management commands."""
    pass


@workflow.command()
@click.argument("workflow_id")
@click.option("--domain", "-d", multiple=True, help="Domain to add (can be used multiple times)")
def create(workflow_id: str, domain: tuple):
    """Create a new workflow."""
    manager = get_workflow_manager()

    try:
        workflow = manager.create_workflow(workflow_id)
        click.secho(f"✓ Created workflow: {workflow_id}", fg="green")

        if domain:
            for domain_id in domain:
                try:
                    workflow.add_domain_spec(domain_id, {})
                    click.secho(f"  ✓ Added domain: {domain_id}", fg="green")
                except ValueError as e:
                    click.secho(f"  ✗ Failed to add domain {domain_id}: {e}", fg="red")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")


@workflow.command()
def list():
    """List all workflows."""
    manager = get_workflow_manager()
    workflows = manager.list_workflows()

    if not workflows:
        click.echo("No workflows created yet")
        return

    click.secho(f"\nWorkflows ({len(workflows)})", fg="cyan", bold=True)
    for wf_id in workflows:
        workflow = manager.get_workflow(wf_id)
        domains = workflow.get_involved_domains()
        click.echo(f"  • {wf_id}: {len(domains)} domains")


@workflow.command()
@click.argument("workflow_id")
def show(workflow_id: str):
    """Show workflow details."""
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)

        click.secho(f"\nWorkflow: {workflow_id}", fg="cyan", bold=True)

        domains = workflow.get_involved_domains()
        click.echo(f"Domains: {len(domains)}")
        if domains:
            for domain_id in domains:
                click.echo(f"  • {domain_id}")

        # Show validation status
        result = workflow.validate()
        click.echo(f"\nValidation Status: {result.status}")

        if result.cross_domain_conflicts:
            click.secho(f"Conflicts: {len(result.cross_domain_conflicts)}", fg="yellow")
            for conflict in result.cross_domain_conflicts:
                click.echo(f"  • {conflict.message}")

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")


@workflow.command()
@click.argument("workflow_id")
@click.argument("domain_id")
def add(workflow_id: str, domain_id: str):
    """Add a domain to a workflow."""
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        workflow.add_domain_spec(domain_id, {})
        click.secho(f"✓ Added domain '{domain_id}' to workflow '{workflow_id}'", fg="green")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")


@workflow.command()
@click.argument("workflow_id")
def validate(workflow_id: str):
    """Validate a workflow."""
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        result = workflow.validate()

        click.secho(
            f"\nValidation Result: {result.status.upper()}",
            fg="green" if result.status == "valid" else "yellow",
        )

        domains = workflow.get_involved_domains()
        click.echo(f"Domains: {', '.join(domains)}")

        if result.cross_domain_conflicts:
            click.secho(f"Conflicts Found: {len(result.cross_domain_conflicts)}", fg="yellow")
            for conflict in result.cross_domain_conflicts:
                severity_color = "red" if conflict.severity == "error" else "yellow"
                click.secho(
                    f"  [{conflict.severity.upper()}] {conflict.message}", fg=severity_color
                )

        click.echo("\nDetails:")
        for key, value in result.summary.items():
            click.echo(f"  {key}: {value}")

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")


@workflow.command()
@click.argument("workflow_id")
@click.option("--format", "-f", default="json", type=click.Choice(["json"]))
def export(workflow_id: str, format: str):
    """Export workflow specification."""
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        exported = workflow.export_specification(format)

        click.echo(json.dumps(exported, indent=2))

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")


@workflow.command()
@click.argument("workflow_id")
def delete(workflow_id: str):
    """Delete a workflow."""
    manager = get_workflow_manager()

    if click.confirm(f"Delete workflow '{workflow_id}'?"):
        try:
            manager.delete_workflow(workflow_id)
            click.secho(f"✓ Deleted workflow: {workflow_id}", fg="green")
        except ValueError as e:
            click.secho(f"Error: {e}", fg="red")


@cli.group()
def analytics():
    """Analytics and reporting commands."""
    pass


@analytics.command()
def report():
    """Get overall analytics report."""
    analytics = get_domain_analytics()
    report = analytics.get_overall_report()

    click.secho("\nAnalytics Report", fg="cyan", bold=True)
    click.echo(f"Generated: {report['created_at']}")

    click.echo("\nDomain Statistics:")
    click.echo(f"  Total Accesses: {report['total_domain_accesses']}")
    click.echo(f"  Questions Answered: {report['total_questions_answered']}")
    click.echo(f"  Exports Generated: {report['total_exports_generated']}")
    click.echo(f"  Conflicts Detected: {report['total_conflicts_detected']}")
    click.echo(f"  Unique Domains Used: {report['unique_domains_count']}")

    if report["domain_reports"]:
        click.echo("\nDomain Breakdown:")
        for domain_id, d in report["domain_reports"].items():
            click.echo(f"  • {domain_id}:")
            click.echo(f"    Accesses: {d['access_count']}")
            click.echo(f"    Questions: {d['questions_answered']}")
            click.echo(f"    Exports: {d['exports_generated']}")
            click.echo(f"    Conflicts: {d['conflicts_detected']}")

    click.echo(f"\nWorkflows Tracked: {report['workflows_tracked']}")


@analytics.command()
def quality():
    """Get quality summary."""
    analytics = get_domain_analytics()
    summary = analytics.get_quality_summary()

    click.secho("\nQuality Summary", fg="cyan", bold=True)
    click.echo(f"Workflows Analyzed: {summary['workflows_analyzed']}")
    click.echo(f"Average Quality Score: {summary['average_quality_score']}/100")
    click.echo(f"Average Completeness: {summary.get('average_completeness', 0)}/100")
    click.echo(f"Total Conflicts: {summary.get('total_conflicts_across_workflows', 0)}")


@analytics.command()
def domains():
    """Show most used domains."""
    analytics = get_domain_analytics()
    most_used = analytics.get_most_used_domains(limit=10)

    if not most_used:
        click.echo("No domain usage data available")
        return

    click.secho("\nMost Used Domains", fg="cyan", bold=True)
    for domain_id, count in most_used:
        click.echo(f"  {domain_id}: {count} accesses")


@analytics.command()
@click.option("--format", "-f", default="json", type=click.Choice(["json"]))
def export(format: str):
    """Export analytics data."""
    analytics = get_domain_analytics()
    exported = analytics.export_analytics(format)

    click.echo(json.dumps(exported, indent=2))


@cli.command()
def version():
    """Show version information."""
    click.echo("Socrates CLI v0.1.0")
    click.echo("Phase 7.4 - Advanced Analytics System")


if __name__ == "__main__":
    cli()
