"""Question management commands.

/question list - List questions in domain
/question create - Create custom question
/question answer - Answer a question
/question show - Show question details
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class QuestionCommandHandler(CommandHandler):
    """Handler for question management commands"""

    command_name = "question"
    description = "Questions: list, create, answer, show"
    help_text = """
[bold cyan]Question Commands:[/bold cyan]
  [yellow]/question list[/yellow]              List domain questions
  [yellow]/question create[/yellow]            Create custom question
  [yellow]/question answer <id>[/yellow]       Answer a question
  [yellow]/question show <id>[/yellow]         Show question details
"""

    def handle(self, args: List[str]) -> None:
        """Route question commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "create":
            self.create()
        elif subcommand == "answer":
            self.answer(args[1:])
        elif subcommand == "show":
            self.show(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List questions in current domain"""
        project = self.ensure_project_selected()
        if not project:
            return

        domain = project.get("domain", "general")
        self.console.print(f"[cyan]Loading {domain} questions...[/cyan]")

        try:
            result = self.api.list_domain_questions(domain)

            if not result.get("success"):
                self.print_error("Failed to load questions")
                return

            questions = result.get("data", {}).get("questions", [])

            if not questions:
                self.console.print(f"[yellow]No questions for {domain} domain[/yellow]")
                return

            self.console.print(f"[bold cyan]Questions for {domain.capitalize()} Domain[/bold cyan]\n")

            for i, q in enumerate(questions, 1):
                q_id = q.get("id", "N/A")
                q_text = q.get("text", "N/A")
                q_type = q.get("type", "open")
                answered = q.get("answered", False)

                answer_status = "[green]✓[/green]" if answered else "[yellow]○[/yellow]"
                self.console.print(f"{answer_status} [{q_type}] {q_text}")
                self.console.print(f"   [dim]ID: {q_id}[/dim]\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def create(self) -> None:
        """Create custom question"""
        project = self.ensure_project_selected()
        if not project:
            return

        session = self.ensure_session_selected()
        if not session:
            return

        self.console.print("[bold cyan]Create Custom Question[/bold cyan]\n")

        try:
            question_text = prompts.prompt_text(self.console, "Question text")

            q_type = prompts.prompt_choice(
                self.console,
                "Question type",
                ["open", "multiple-choice", "ranking", "essay"],
                default="open"
            )

            category = prompts.prompt_text(
                self.console,
                "Category (optional)",
                default=""
            )

            tags = prompts.prompt_text(
                self.console,
                "Tags (comma-separated, optional)",
                default=""
            )

            self.console.print("[cyan]Creating question...[/cyan]")

            result = self.api.create_custom_question(
                session.get("id"),
                text=question_text,
                q_type=q_type,
                category=category,
                tags=[t.strip() for t in tags.split(",") if t.strip()]
            )

            if result.get("success"):
                self.print_success(f"Question created: {question_text}")
                self.console.print(f"[cyan]Question ID: {result.get('question_id')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Creation cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def answer(self, args: List[str]) -> None:
        """Answer a question"""
        project = self.ensure_project_selected()
        if not project:
            return

        session = self.ensure_session_selected()
        if not session:
            return

        if not args:
            self.console.print("[yellow]Usage: /question answer <question_id>[/yellow]")
            return

        question_id = args[0]

        try:
            # Get question details
            result = self.api.get_question(question_id)

            if not result.get("success"):
                self.print_error("Question not found")
                return

            question = result.get("data")
            self.console.print(f"\n[bold cyan]{question.get('text')}[/bold cyan]\n")

            # Get answer based on type
            q_type = question.get("type", "open")

            if q_type == "multiple-choice":
                choices = question.get("choices", [])
                answer = prompts.prompt_choice(
                    self.console,
                    "Your answer",
                    choices,
                )
            elif q_type == "ranking":
                items = question.get("items", [])
                answer = prompts.select_multiple_from_list(
                    self.console,
                    "Rank items",
                    items,
                    "Select items in order (top to bottom)"
                )
            else:  # open or essay
                answer = prompts.prompt_text(self.console, "Your answer")

            # Save answer
            save_result = self.api.submit_question_answer(
                session.get("id"),
                question_id,
                answer=answer
            )

            if save_result.get("success"):
                self.print_success("Answer recorded")
            else:
                error = save_result.get("error") or "Unknown error"
                self.print_error(f"Failed to save: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def show(self, args: List[str]) -> None:
        """Show question details"""
        if not args:
            self.console.print("[yellow]Usage: /question show <question_id>[/yellow]")
            return

        question_id = args[0]

        try:
            result = self.api.get_question(question_id)

            if not result.get("success"):
                self.print_error("Question not found")
                return

            question = result.get("data")

            self.console.print(f"\n[bold cyan]{question.get('text')}[/bold cyan]\n")

            from cli.utils.table_formatter import format_key_value_table

            question_data = {
                "ID": question.get("id", "N/A"),
                "Type": question.get("type", "N/A"),
                "Category": question.get("category", "N/A"),
                "Domain": question.get("domain", "N/A"),
                "Answered": "Yes" if question.get("answered") else "No",
                "Created": question.get("created_at", "N/A"),
            }

            table = format_key_value_table(question_data)
            self.console.print(table)

            # Show choices if multiple choice
            if question.get("type") == "multiple-choice":
                self.console.print("\n[bold]Options:[/bold]")
                for choice in question.get("choices", []):
                    self.console.print(f"  • {choice}")

        except Exception as e:
            self.print_error(f"Error: {e}")
