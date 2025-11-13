"""Search functionality commands.

/search text - Full-text search
/search semantic - Semantic search
/search specifications - Search specifications
/search advanced - Advanced search with filters
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class SearchCommandHandler(CommandHandler):
    """Handler for search commands"""

    command_name = "search"
    description = "Search: text, semantic, specifications, advanced"
    help_text = """
[bold cyan]Search Commands:[/bold cyan]
  [yellow]/search text <query>[/yellow]           Full-text search
  [yellow]/search semantic <query>[/yellow]      Semantic search
  [yellow]/search specifications <query>[/yellow] Search specifications
  [yellow]/search advanced[/yellow]              Advanced search with filters
"""

    def handle(self, args: List[str]) -> None:
        """Route search commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "text":
            self.text_search(args[1:])
        elif subcommand == "semantic":
            self.semantic_search(args[1:])
        elif subcommand == "specifications":
            self.search_specifications(args[1:])
        elif subcommand == "advanced":
            self.advanced_search()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def text_search(self, args: List[str]) -> None:
        """Full-text search"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            query = prompts.prompt_text(self.console, "Search query")
        else:
            query = " ".join(args)

        self.console.print("[cyan]Searching...[/cyan]")

        try:
            result = self.api.text_search(project.get("id"), query)

            if not result.get("success"):
                self.print_error("Search failed")
                return

            results = result.get("data", {}).get("results", [])

            if not results:
                self.console.print(f"[yellow]No results found for '{query}'[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Text Search Results for: {query}[/bold cyan] ({len(results)} results)\n")

            for i, match in enumerate(results, 1):
                title = match.get("title", "Unknown")
                match_type = match.get("type", "N/A")
                excerpt = match.get("excerpt", "")[:150]
                relevance = match.get("relevance_score", 0)

                self.console.print(f"[yellow]{i}.[/yellow] [bold]{title}[/bold]")
                self.console.print(f"   Type: {match_type} | Relevance: {relevance:.2f}")
                self.console.print(f"   {excerpt}...\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def semantic_search(self, args: List[str]) -> None:
        """Semantic search"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            query = prompts.prompt_text(self.console, "Search query")
        else:
            query = " ".join(args)

        self.console.print("[cyan]Performing semantic search...[/cyan]")

        try:
            result = self.api.semantic_search(project.get("id"), query)

            if not result.get("success"):
                self.print_error("Search failed")
                return

            results = result.get("data", {}).get("results", [])

            if not results:
                self.console.print(f"[yellow]No similar content found for '{query}'[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Semantic Search Results for: {query}[/bold cyan] ({len(results)} results)\n")

            for i, match in enumerate(results, 1):
                title = match.get("title", "Unknown")
                similarity = match.get("similarity_score", 0)
                excerpt = match.get("excerpt", "")[:150]
                source = match.get("source", "N/A")

                self.console.print(f"[yellow]{i}.[/yellow] [bold]{title}[/bold]")
                self.console.print(f"   Source: {source} | Similarity: {similarity:.2f}")
                self.console.print(f"   {excerpt}...\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def search_specifications(self, args: List[str]) -> None:
        """Search specifications"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            query = prompts.prompt_text(self.console, "Search specifications")
        else:
            query = " ".join(args)

        # Get additional filters
        filters = {}
        apply_filters = prompts.prompt_confirm(
            self.console,
            "Apply additional filters?",
            default=False
        )

        if apply_filters:
            status = prompts.prompt_choice(
                self.console,
                "Status (optional)",
                ["any", "draft", "approved", "implemented"],
                default="any"
            )
            if status != "any":
                filters["status"] = status

            spec_type = prompts.prompt_choice(
                self.console,
                "Type (optional)",
                ["any", "feature", "bug", "enhancement", "documentation"],
                default="any"
            )
            if spec_type != "any":
                filters["type"] = spec_type

        self.console.print("[cyan]Searching specifications...[/cyan]")

        try:
            result = self.api.search_specifications(project.get("id"), query, filters=filters)

            if not result.get("success"):
                self.print_error("Search failed")
                return

            specs = result.get("data", {}).get("specifications", [])

            if not specs:
                self.console.print(f"[yellow]No specifications match your query[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Specification Search Results ({len(specs)} found)[/bold cyan]\n")

            for spec in specs:
                title = spec.get("title", "Unknown")
                status = spec.get("status", "draft")
                spec_type = spec.get("type", "feature")
                created = spec.get("created_at", "N/A")

                status_color = "green" if status == "implemented" else "yellow" if status == "approved" else "white"
                self.console.print(f"[yellow]•[/yellow] [bold]{title}[/bold]")
                self.console.print(f"   Type: {spec_type} | Status: [{status_color}]{status}[/{status_color}] | Created: {created}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def advanced_search(self) -> None:
        """Advanced search with filters"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Advanced Search[/bold cyan]\n")

        # Get search parameters
        query = prompts.prompt_text(self.console, "Search query (or leave empty)")

        search_in = prompts.select_multiple_from_list(
            self.console,
            "Search in",
            ["specifications", "documents", "code", "conversation"],
            "Select where to search"
        )

        date_range = prompts.prompt_choice(
            self.console,
            "Date range",
            ["any", "today", "this-week", "this-month", "this-year"],
            default="any"
        )

        # Additional filters based on search scope
        filters = {
            "search_in": search_in,
            "date_range": date_range
        }

        if "specifications" in search_in:
            spec_status = prompts.select_multiple_from_list(
                self.console,
                "Specification status",
                ["draft", "approved", "implemented"],
                "Select status to include"
            )
            if spec_status:
                filters["spec_status"] = spec_status

        if "code" in search_in:
            language = prompts.prompt_text(
                self.console,
                "Programming language (optional)",
                default=""
            )
            if language:
                filters["language"] = language

        self.console.print("[cyan]Performing advanced search...[/cyan]")

        try:
            result = self.api.advanced_search(project.get("id"), query or "*", filters=filters)

            if not result.get("success"):
                self.print_error("Search failed")
                return

            results = result.get("data", {}).get("results", [])

            if not results:
                self.console.print("[yellow]No results found[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Advanced Search Results ({len(results)} found)[/bold cyan]\n")

            for i, match in enumerate(results, 1):
                title = match.get("title", "Unknown")
                match_type = match.get("type", "N/A")
                relevance = match.get("relevance_score", 0)
                excerpt = match.get("excerpt", "")[:100]

                self.console.print(f"[yellow]{i}.[/yellow] [bold]{title}[/bold]")
                self.console.print(f"   Type: {match_type} | Relevance: {relevance:.2f}")
                self.console.print(f"   {excerpt}...\n")

        except Exception as e:
            self.print_error(f"Error: {e}")
