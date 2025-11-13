"""Domain management and discovery commands.

/domain list - List all available domains
/domain info - Show domain details
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import constants, table_formatter


class DomainCommandHandler(CommandHandler):
    """Handler for domain management commands"""

    command_name = "domain"
    description = "Domain discovery: list, info"
    help_text = """
[bold cyan]Domain Commands:[/bold cyan]
  [yellow]/domain list[/yellow]        List all available domains
  [yellow]/domain info <domain>[/yellow] Show domain details
"""

    def handle(self, args: List[str]) -> None:
        """Route domain commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "info":
            self.info(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List all available domains"""
        self.console.print("[bold cyan]Available Domains[/bold cyan]\n")

        for domain_key, domain_info in sorted(constants.DOMAINS.items()):
            icon = domain_info.get("icon", "•")
            name = domain_info.get("name", domain_key)
            desc = domain_info.get("description", "")

            self.console.print(f"{icon} [bold]{name}[/bold]")
            self.console.print(f"   {desc}\n")

        self.console.print("[yellow]Use /domain info <domain> for details[/yellow]")

    def info(self, args: List[str]) -> None:
        """Show domain information"""
        if not args:
            self.console.print("[yellow]Usage: /domain info <domain>[/yellow]")
            return

        domain_key = args[0].lower()

        if domain_key not in constants.DOMAINS:
            self.print_error(f"Domain not found: {domain_key}")
            self.console.print("[yellow]Available domains: " +
                             ", ".join(constants.DOMAINS.keys()) + "[/yellow]")
            return

        domain = constants.DOMAINS[domain_key]

        self.console.print(f"\n[bold cyan]{domain.get('name')}[/bold cyan]\n")
        self.console.print(f"{domain.get('icon')} {domain.get('description')}\n")

        self.console.print("[dim]This domain includes:[/dim]")
        self.console.print("[dim]• Domain-specific questions[/dim]")
        self.console.print("[dim]• Tailored workflows[/dim]")
        self.console.print("[dim]• Custom output formats[/dim]")
        self.console.print("[dim]• Appropriate templates[/dim]")
