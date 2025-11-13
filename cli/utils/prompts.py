"""
Prompt utilities shared across CLI commands.

Contains functions for common user prompts and input collection.
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table


def prompt_choice(
    console: Console,
    question: str,
    choices: List[str],
    default: str = None
) -> str:
    """
    Prompt user to choose from a list of options.

    Args:
        console: Rich console
        question: Question to ask
        choices: List of valid choices
        default: Default choice if user just presses Enter

    Returns:
        Selected choice
    """
    return Prompt.ask(
        question,
        choices=choices,
        default=default,
        console=console
    )


def prompt_confirm(
    console: Console,
    question: str,
    default: bool = False
) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        console: Rich console
        question: Question to ask
        default: Default value

    Returns:
        True if user confirms, False otherwise
    """
    return Confirm.ask(
        question,
        default=default,
        console=console
    )


def prompt_text(
    console: Console,
    question: str,
    default: str = None,
    password: bool = False
) -> str:
    """
    Prompt user for text input.

    Args:
        console: Rich console
        question: Question to ask
        default: Default value
        password: If True, hide input

    Returns:
        User input
    """
    return Prompt.ask(
        question,
        default=default,
        password=password,
        console=console
    )


def prompt_email(
    console: Console,
    question: str = "Email address"
) -> str:
    """
    Prompt user for email address.

    Args:
        console: Rich console
        question: Question to ask

    Returns:
        Email address
    """
    while True:
        email = Prompt.ask(question, console=console)
        if "@" in email and "." in email:
            return email
        console.print("[red]✗ Invalid email format. Please try again.[/red]")


def select_from_list(
    console: Console,
    items: List[Dict[str, Any]],
    id_key: str = "id",
    display_key: str = "name",
    title: str = "Select an item"
) -> Optional[Dict[str, Any]]:
    """
    Display a list of items and let user select one.

    Args:
        console: Rich console
        items: List of items (dicts)
        id_key: Key to use for identifying items
        display_key: Key to use for display text
        title: Title for the selection

    Returns:
        Selected item dict or None if user cancels
    """
    if not items:
        console.print("[yellow]No items to select from[/yellow]")
        return None

    console.print(f"\n[bold cyan]{title}:[/bold cyan]")

    for i, item in enumerate(items, 1):
        display = item.get(display_key, str(item.get(id_key, "?")))
        console.print(f"  [{i}] {display}")

    console.print(f"  [back] Cancel\n")

    choice = Prompt.ask(
        "Select",
        choices=[str(i) for i in range(1, len(items) + 1)] + ["back"],
        default="back",
        console=console
    )

    if choice == "back":
        return None

    try:
        index = int(choice) - 1
        return items[index]
    except (ValueError, IndexError):
        console.print("[red]✗ Invalid selection[/red]")
        return None


def select_multiple_from_list(
    console: Console,
    items: List[Dict[str, Any]],
    id_key: str = "id",
    display_key: str = "name",
    title: str = "Select items",
    min_selections: int = 1
) -> List[Dict[str, Any]]:
    """
    Display a list and let user select multiple items.

    Args:
        console: Rich console
        items: List of items (dicts)
        id_key: Key to use for identifying items
        display_key: Key to use for display text
        title: Title for the selection
        min_selections: Minimum required selections

    Returns:
        List of selected items
    """
    if not items:
        console.print("[yellow]No items to select from[/yellow]")
        return []

    selected = []

    while len(selected) < min_selections:
        console.print(f"\n[bold cyan]{title}:[/bold cyan]")
        console.print(f"[yellow](Selected: {len(selected)})[/yellow]\n")

        for i, item in enumerate(items, 1):
            if item in selected:
                display = item.get(display_key, str(item.get(id_key, "?")))
                console.print(f"  [{i}] ✓ {display}")
            else:
                display = item.get(display_key, str(item.get(id_key, "?")))
                console.print(f"  [{i}] {display}")

        console.print(f"\n  [done] Done selecting")
        console.print(f"  [cancel] Cancel\n")

        choice = Prompt.ask("Select", console=console)

        if choice == "done":
            if len(selected) >= min_selections:
                break
            else:
                console.print(
                    f"[red]✗ Please select at least {min_selections} item(s)[/red]"
                )
        elif choice == "cancel":
            return []
        else:
            try:
                index = int(choice) - 1
                item = items[index]
                if item in selected:
                    selected.remove(item)
                else:
                    selected.append(item)
            except (ValueError, IndexError):
                console.print("[red]✗ Invalid selection[/red]")

    return selected


def prompt_for_table_selection(
    console: Console,
    table_data: List[Dict[str, Any]],
    display_columns: List[str],
    id_column: str = "id",
    title: str = "Select item"
) -> Optional[Dict[str, Any]]:
    """
    Display table and let user select a row.

    Args:
        console: Rich console
        table_data: List of row dicts
        display_columns: Columns to display
        id_column: Key containing item ID
        title: Table title

    Returns:
        Selected row dict or None
    """
    if not table_data:
        console.print("[yellow]No items available[/yellow]")
        return None

    table = Table(title=title, show_header=True, header_style="bold cyan")

    # Add number column
    table.add_column("#", style="yellow")

    # Add data columns
    for col in display_columns:
        table.add_column(col, style="cyan")

    # Add rows
    for i, row in enumerate(table_data, 1):
        row_values = [str(i)]
        for col in display_columns:
            value = row.get(col, "")
            # Truncate long values
            if isinstance(value, str) and len(value) > 40:
                value = value[:37] + "..."
            row_values.append(str(value))
        table.add_row(*row_values)

    console.print(table)
    console.print(f"  [back] Cancel\n")

    choice = Prompt.ask(
        "Select",
        choices=[str(i) for i in range(1, len(table_data) + 1)] + ["back"],
        default="back",
        console=console
    )

    if choice == "back":
        return None

    try:
        index = int(choice) - 1
        return table_data[index]
    except (ValueError, IndexError):
        console.print("[red]✗ Invalid selection[/red]")
        return None
