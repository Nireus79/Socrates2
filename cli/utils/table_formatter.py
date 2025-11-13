"""
Table formatting utilities for displaying data in CLI.

Contains functions for creating and formatting Rich tables for common data types.
"""

from typing import List, Dict, Any, Optional
from rich.table import Table
from cli.utils.helpers import truncate_string, format_datetime


def create_table(
    title: str = None,
    columns: List[Dict[str, Any]] = None,
    rows: List[List[str]] = None
) -> Table:
    """
    Create a Rich table with given configuration.

    Args:
        title: Table title
        columns: List of column dicts with keys: name, style, width
        rows: List of row data (each row is a list of values)

    Returns:
        Rich Table object
    """
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="cyan"
    )

    # Add columns
    if columns:
        for col in columns:
            table.add_column(
                col.get("name", "Column"),
                style=col.get("style", ""),
                width=col.get("width")
            )

    # Add rows
    if rows:
        for row in rows:
            table.add_row(*[str(v) for v in row])

    return table


def format_project_table(projects: List[Dict[str, Any]]) -> Table:
    """
    Format projects list as table.

    Args:
        projects: List of project dicts

    Returns:
        Rich Table
    """
    table = Table(title="Projects", show_header=True, header_style="bold cyan")

    table.add_column("#", style="yellow", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Type", style="blue")
    table.add_column("Created", style="white")

    for i, project in enumerate(projects, 1):
        # Determine project type
        project_type = "Team" if project.get("team_id") else "Solo"

        # Determine status color
        status = project.get("status", "unknown")
        if status == "active":
            status_colored = "[green]Active[/green]"
        elif status == "archived":
            status_colored = "[yellow]Archived[/yellow]"
        elif status == "completed":
            status_colored = "[cyan]Completed[/cyan]"
        else:
            status_colored = status

        created = format_datetime(project.get("created_at"), "%Y-%m-%d")

        table.add_row(
            str(i),
            truncate_string(project.get("name", "Unknown"), 30),
            project.get("domain", "N/A"),
            status_colored,
            project_type,
            created
        )

    return table


def format_session_table(sessions: List[Dict[str, Any]]) -> Table:
    """
    Format sessions list as table.

    Args:
        sessions: List of session dicts

    Returns:
        Rich Table
    """
    table = Table(title="Sessions", show_header=True, header_style="bold cyan")

    table.add_column("#", style="yellow", width=3)
    table.add_column("Name/ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Mode", style="blue")
    table.add_column("Messages", style="white")
    table.add_column("Started", style="white")

    for i, session in enumerate(sessions, 1):
        session_id = truncate_string(session.get("id", "Unknown"), 20)
        status = session.get("status", "active")
        mode = session.get("mode", "socratic")
        message_count = session.get("message_count", 0)
        created = format_datetime(session.get("created_at"), "%Y-%m-%d %H:%M")

        # Status colors
        if status == "active":
            status_colored = "[green]Active[/green]"
        elif status == "paused":
            status_colored = "[yellow]Paused[/yellow]"
        elif status == "ended":
            status_colored = "[red]Ended[/red]"
        else:
            status_colored = status

        table.add_row(
            str(i),
            session_id,
            status_colored,
            mode,
            str(message_count),
            created
        )

    return table


def format_team_table(teams: List[Dict[str, Any]]) -> Table:
    """
    Format teams list as table.

    Args:
        teams: List of team dicts

    Returns:
        Rich Table
    """
    table = Table(title="Teams", show_header=True, header_style="bold cyan")

    table.add_column("#", style="yellow", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Your Role", style="blue")
    table.add_column("Members", style="green")
    table.add_column("Projects", style="white")
    table.add_column("Created", style="white")

    for i, team in enumerate(teams, 1):
        name = truncate_string(team.get("name", "Unknown"), 30)
        role = team.get("your_role", "member").title()
        members = team.get("member_count", 0)
        projects = team.get("project_count", 0)
        created = format_datetime(team.get("created_at"), "%Y-%m-%d")

        table.add_row(
            str(i),
            name,
            role,
            str(members),
            str(projects),
            created
        )

    return table


def format_specification_table(specs: List[Dict[str, Any]]) -> Table:
    """
    Format specifications list as table.

    Args:
        specs: List of specification dicts

    Returns:
        Rich Table
    """
    table = Table(title="Specifications", show_header=True, header_style="bold cyan")

    table.add_column("#", style="yellow", width=3)
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Created", style="white")

    for i, spec in enumerate(specs, 1):
        title = truncate_string(spec.get("title", "Unknown"), 40)
        spec_type = spec.get("type", "general")
        status = spec.get("status", "draft")

        # Status colors
        if status == "approved":
            status_colored = "[green]Approved[/green]"
        elif status == "draft":
            status_colored = "[yellow]Draft[/yellow]"
        elif status == "implemented":
            status_colored = "[cyan]Implemented[/cyan]"
        else:
            status_colored = status

        created = format_datetime(spec.get("created_at"), "%Y-%m-%d")

        table.add_row(
            str(i),
            title,
            spec_type,
            status_colored,
            created
        )

    return table


def format_member_table(members: List[Dict[str, Any]]) -> Table:
    """
    Format team members list as table.

    Args:
        members: List of member dicts

    Returns:
        Rich Table
    """
    table = Table(title="Team Members", show_header=True, header_style="bold cyan")

    table.add_column("Name", style="cyan")
    table.add_column("Email", style="blue")
    table.add_column("Role", style="magenta")
    table.add_column("Joined", style="white")

    for member in members:
        name = member.get("name", member.get("email", "Unknown"))
        email = member.get("email", "N/A")
        role = member.get("role", "member").title()
        joined = format_datetime(member.get("joined_at"), "%Y-%m-%d")

        table.add_row(name, email, role, joined)

    return table


def format_activity_table(activities: List[Dict[str, Any]]) -> Table:
    """
    Format activity/collaboration status as table.

    Args:
        activities: List of activity dicts

    Returns:
        Rich Table
    """
    table = Table(title="Recent Activity", show_header=True, header_style="bold cyan")

    table.add_column("User", style="cyan")
    table.add_column("Action", style="blue")
    table.add_column("Object", style="magenta")
    table.add_column("Time", style="white")

    for activity in activities:
        user = activity.get("user_name", "Unknown")
        action = activity.get("action", "updated")
        obj = truncate_string(activity.get("object_name", "Unknown"), 30)
        time = format_datetime(activity.get("created_at"), "%H:%M:%S")

        table.add_row(user, action, obj, time)

    return table


def format_key_value_table(data: Dict[str, Any], title: str = "Details") -> Table:
    """
    Format key-value data as two-column table.

    Args:
        data: Dictionary of key-value pairs
        title: Table title

    Returns:
        Rich Table
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for key, value in data.items():
        # Format key (title case, replace underscores)
        formatted_key = key.replace("_", " ").title()

        # Format value
        if isinstance(value, dict):
            formatted_value = str(value)
        elif isinstance(value, list):
            formatted_value = ", ".join(str(v) for v in value)
        else:
            formatted_value = str(value) if value is not None else "N/A"

        # Truncate if too long
        if len(formatted_value) > 60:
            formatted_value = truncate_string(formatted_value, 60)

        table.add_row(formatted_key, formatted_value)

    return table
