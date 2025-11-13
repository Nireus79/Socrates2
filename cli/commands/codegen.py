"""Code generation commands.

/codegen generate - Generate code from specification
/codegen status - Check generation status
/codegen download - Download generated code
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class CodegenCommandHandler(CommandHandler):
    """Handler for code generation commands"""

    command_name = "codegen"
    description = "Code generation: generate, status, download"
    help_text = """
[bold cyan]Code Generation Commands:[/bold cyan]
  [yellow]/codegen generate[/yellow]      Generate code from specification
  [yellow]/codegen status[/yellow]        Check generation status
  [yellow]/codegen download <id>[/yellow] Download generated code
"""

    def handle(self, args: List[str]) -> None:
        """Route code generation commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "generate":
            self.generate()
        elif subcommand == "status":
            self.status(args[1:])
        elif subcommand == "download":
            self.download(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def generate(self) -> None:
        """Generate code from specification"""
        project = self.ensure_project_selected()
        if not project:
            return

        session = self.ensure_session_selected()
        if not session:
            return

        self.console.print("[bold cyan]Code Generation[/bold cyan]\n")

        try:
            # Get target language
            language = prompts.prompt_choice(
                self.console,
                "Target language",
                ["python", "javascript", "typescript", "java", "go", "rust", "csharp"],
                default="python"
            )

            # Get architecture pattern
            pattern = prompts.prompt_choice(
                self.console,
                "Architecture pattern",
                ["mvc", "rest-api", "microservices", "serverless", "monolithic"],
                default="rest-api"
            )

            # Get framework (language-specific)
            framework_options = self._get_framework_options(language)
            framework = prompts.prompt_choice(
                self.console,
                "Framework",
                framework_options,
                default=framework_options[0]
            )

            # Get additional features
            features = prompts.select_multiple_from_list(
                self.console,
                "Additional features",
                ["testing", "documentation", "docker", "ci-cd", "database-models", "api-docs"],
                "Select features to include"
            )

            self.console.print("[cyan]Generating code...[/cyan]")

            result = self.api.generate_code(
                session.get("id"),
                language=language,
                pattern=pattern,
                framework=framework,
                features=features
            )

            if result.get("success"):
                self.print_success("Code generation started")
                self.console.print(f"[cyan]Generation ID: {result.get('generation_id')}[/cyan]")
                self.console.print(f"[cyan]Estimated time: {result.get('estimated_time')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Generation cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def status(self, args: List[str]) -> None:
        """Check code generation status"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading generation statuses...[/cyan]")

        try:
            result = self.api.list_code_generations(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load generations")
                return

            generations = result.get("data", {}).get("generations", [])

            if not generations:
                self.console.print("[yellow]No code generations yet[/yellow]")
                return

            self.console.print("[bold cyan]Code Generations[/bold cyan]\n")

            for gen in generations:
                gen_id = gen.get("id", "N/A")
                language = gen.get("language", "N/A")
                status = gen.get("status", "pending")
                progress = gen.get("progress", 0)
                created = gen.get("created_at", "N/A")

                status_color = "green" if status == "completed" else "yellow" if status == "in-progress" else "red"
                self.console.print(f"[yellow]ID:[/yellow] {gen_id}")
                self.console.print(f"[yellow]Language:[/yellow] {language}")
                self.console.print(f"[yellow]Status:[/yellow] [{status_color}]{status}[/{status_color}]")
                self.console.print(f"[yellow]Progress:[/yellow] {progress}%")
                self.console.print(f"[yellow]Created:[/yellow] {created}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def download(self, args: List[str]) -> None:
        """Download generated code"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /codegen download <generation_id>[/yellow]")
            return

        gen_id = args[0]

        try:
            result = self.api.download_generated_code(gen_id)

            if result.get("success"):
                self.print_success("Code downloaded successfully")
                self.console.print(f"[cyan]File: {result.get('filename')}[/cyan]")
                self.console.print(f"[cyan]Size: {result.get('file_size')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    @staticmethod
    def _get_framework_options(language: str) -> List[str]:
        """Get framework options for language"""
        frameworks = {
            "python": ["FastAPI", "Django", "Flask", "SQLAlchemy"],
            "javascript": ["Express", "Next.js", "NestJS", "Hapi"],
            "typescript": ["Express", "NestJS", "Fastify", "tsyringe"],
            "java": ["Spring Boot", "Quarkus", "Micronaut", "Eclipse"],
            "go": ["Gin", "Echo", "Fiber", "Chi"],
            "rust": ["Actix", "Rocket", "Axum", "Warp"],
            "csharp": ["ASP.NET Core", "Nancy", "ServiceStack", "OpenAPI"],
        }
        return frameworks.get(language.lower(), ["Standard"])
