"""GitHub integration commands.

/github connect - Connect GitHub account
/github import - Import from GitHub repository
/github analyze - Analyze GitHub repository
/github sync - Sync with GitHub
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class GitHubCommandHandler(CommandHandler):
    """Handler for GitHub integration commands"""

    command_name = "github"
    description = "GitHub: connect, import, analyze, sync"
    help_text = """
[bold cyan]GitHub Commands:[/bold cyan]
  [yellow]/github connect[/yellow]            Connect GitHub account
  [yellow]/github import <repo>[/yellow]      Import from GitHub repository
  [yellow]/github analyze <repo>[/yellow]     Analyze GitHub repository
  [yellow]/github sync[/yellow]               Sync with GitHub
"""

    def handle(self, args: List[str]) -> None:
        """Route github commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "connect":
            self.connect()
        elif subcommand == "import":
            self.import_repo(args[1:])
        elif subcommand == "analyze":
            self.analyze(args[1:])
        elif subcommand == "sync":
            self.sync()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def connect(self) -> None:
        """Connect GitHub account"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[bold cyan]Connect GitHub Account[/bold cyan]\n")

        # Check if already connected
        try:
            result = self.api.get_github_connection_status()

            if result.get("success"):
                status = result.get("data", {}).get("connected", False)
                if status:
                    self.console.print("[green]✓[/green] GitHub account already connected")
                    self.console.print(f"[cyan]User: {result.get('data', {}).get('github_user')}[/cyan]")
                    return

        except Exception as e:
            pass

        # Request connection
        self.console.print("[cyan]To connect your GitHub account, visit:[/cyan]")
        self.console.print("[bold cyan]https://socrates.dev/github/auth[/bold cyan]\n")

        # Get authorization code
        auth_code = prompts.prompt_text(self.console, "Enter authorization code from GitHub")

        try:
            self.console.print("[cyan]Connecting to GitHub...[/cyan]")

            result = self.api.connect_github(auth_code)

            if result.get("success"):
                self.print_success("GitHub account connected")
                self.console.print(f"[cyan]User: {result.get('github_user')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def import_repo(self, args: List[str]) -> None:
        """Import from GitHub repository"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            repo_url = prompts.prompt_text(self.console, "GitHub repository URL (owner/repo)")
        else:
            repo_url = args[0]

        # Get import options
        import_what = prompts.select_multiple_from_list(
            self.console,
            "Import from repository",
            ["readme", "code-structure", "issues", "pull-requests", "documentation"],
            "Select what to import"
        )

        try:
            self.console.print("[cyan]Importing from GitHub...[/cyan]")

            result = self.api.import_from_github(
                project.get("id"),
                repo_url=repo_url,
                import_items=import_what
            )

            if result.get("success"):
                self.print_success(f"Repository imported: {repo_url}")
                self.console.print(f"[cyan]Files imported: {result.get('files_imported', 0)}[/cyan]")
                self.console.print(f"[cyan]Issues imported: {result.get('issues_imported', 0)}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def analyze(self, args: List[str]) -> None:
        """Analyze GitHub repository"""
        if not args:
            repo_url = prompts.prompt_text(self.console, "GitHub repository URL (owner/repo)")
        else:
            repo_url = args[0]

        self.console.print("[cyan]Analyzing repository...[/cyan]")

        try:
            result = self.api.analyze_github_repo(repo_url)

            if not result.get("success"):
                self.print_error("Failed to analyze repository")
                return

            analysis = result.get("data", {})

            self.console.print(f"\n[bold cyan]Repository Analysis: {repo_url}[/bold cyan]\n")

            # Basic info
            info = analysis.get("info", {})
            self.console.print("[bold]Repository Info:[/bold]")
            self.console.print(f"  Language: {info.get('primary_language', 'N/A')}")
            self.console.print(f"  Stars: {info.get('stars', 0)}")
            self.console.print(f"  Forks: {info.get('forks', 0)}")
            self.console.print(f"  Last update: {info.get('last_updated', 'N/A')}\n")

            # Code metrics
            code = analysis.get("code_metrics", {})
            self.console.print("[bold]Code Metrics:[/bold]")
            self.console.print(f"  Total lines: {code.get('lines_of_code', 0)}")
            self.console.print(f"  Files: {code.get('file_count', 0)}")
            self.console.print(f"  Branches: {code.get('branch_count', 0)}")
            self.console.print(f"  Test coverage: {code.get('test_coverage', 'N/A')}%\n")

            # Activity
            activity = analysis.get("activity", {})
            self.console.print("[bold]Activity:[/bold]")
            self.console.print(f"  Commits (last month): {activity.get('commits_last_month', 0)}")
            self.console.print(f"  Contributors: {activity.get('contributor_count', 0)}")
            self.console.print(f"  Open issues: {activity.get('open_issues', 0)}")
            self.console.print(f"  Pull requests: {activity.get('open_prs', 0)}\n")

            # Dependencies
            deps = analysis.get("dependencies", {})
            self.console.print("[bold]Dependencies:[/bold]")
            self.console.print(f"  Direct: {deps.get('direct_count', 0)}")
            self.console.print(f"  Transitive: {deps.get('transitive_count', 0)}")
            self.console.print(f"  Outdated: {deps.get('outdated_count', 0)}")
            self.console.print(f"  Vulnerable: {deps.get('vulnerable_count', 0)}\n")

            # Quality score
            quality = analysis.get("quality", {})
            self.console.print("[bold]Quality Score: {}/100[/bold]".format(quality.get("score", 0)))

        except Exception as e:
            self.print_error(f"Error: {e}")

    def sync(self) -> None:
        """Sync project with GitHub"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Sync with GitHub[/bold cyan]\n")

        try:
            # Check if GitHub connection exists
            result = self.api.get_github_connection_status()

            if not result.get("success") or not result.get("data", {}).get("connected"):
                self.print_error("GitHub account not connected. Use /github connect first.")
                return

            # Get sync options
            sync_direction = prompts.prompt_choice(
                self.console,
                "Sync direction",
                ["push", "pull", "bidirectional"],
                default="push"
            )

            sync_items = prompts.select_multiple_from_list(
                self.console,
                "Items to sync",
                ["specifications", "code", "documentation", "issues"],
                "Select items to sync"
            )

            # Get repository info
            repo_url = prompts.prompt_text(self.console, "Target GitHub repository (owner/repo)")

            if not prompts.prompt_confirm(
                self.console,
                f"Sync {sync_direction} with {repo_url}?",
                default=True
            ):
                self.console.print("[yellow]Cancelled[/yellow]")
                return

            self.console.print("[cyan]Syncing with GitHub...[/cyan]")

            result = self.api.sync_with_github(
                project.get("id"),
                repo_url=repo_url,
                direction=sync_direction,
                items=sync_items
            )

            if result.get("success"):
                self.print_success("Sync completed successfully")
                self.console.print(f"[cyan]Files synced: {result.get('files_synced', 0)}[/cyan]")
                self.console.print(f"[cyan]Issues synced: {result.get('issues_synced', 0)}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
