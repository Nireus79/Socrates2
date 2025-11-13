"""LLM/Model selection commands.

/llm list - List available LLM models
/llm current - Show currently selected model
/llm select - Select LLM provider and model
/llm usage - Show LLM usage statistics
/llm costs - Show cost estimates per model
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class LLMCommandHandler(CommandHandler):
    """Handler for LLM/Model selection commands"""

    command_name = "llm"
    description = "LLM: list, current, select, usage, costs"
    help_text = """
[bold cyan]LLM Commands:[/bold cyan]
  [yellow]/llm list[/yellow]              List available LLM models
  [yellow]/llm current[/yellow]           Show currently selected model
  [yellow]/llm select[/yellow]            Select LLM provider and model
  [yellow]/llm usage[/yellow]             Show LLM usage statistics
  [yellow]/llm costs[/yellow]             Show cost estimates per model
"""

    def handle(self, args: List[str]) -> None:
        """Route LLM commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list_models()
        elif subcommand == "current":
            self.show_current()
        elif subcommand == "select":
            self.select_model()
        elif subcommand == "usage":
            self.show_usage()
        elif subcommand == "costs":
            self.show_costs()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list_models(self) -> None:
        """List available LLM models"""
        self.console.print("[cyan]Loading available LLM models...[/cyan]")

        try:
            result = self.api.list_available_llms()

            if not result.get("success"):
                self.print_error("Failed to load available models")
                return

            data = result.get("data", {})
            providers = data.get("providers", {})

            if not providers:
                self.console.print("[yellow]No LLM providers configured[/yellow]")
                return

            self.console.print("[bold cyan]Available LLM Providers and Models[/bold cyan]\n")

            for provider, models in providers.items():
                self.console.print(f"[bold yellow]{provider.upper()}[/bold yellow]")
                for model in models:
                    name = model.get("name", "Unknown")
                    description = model.get("description", "")
                    context_window = model.get("context_window", "N/A")
                    cost_per_1k = model.get("cost_per_1k_tokens", "N/A")

                    self.console.print(f"  [cyan]•[/cyan] {name}")
                    if description:
                        self.console.print(f"    {description}")
                    self.console.print(f"    Context: {context_window} | Cost: ${cost_per_1k}/1K tokens")
                self.console.print()

        except Exception as e:
            self.print_error(f"Error: {e}")

    def show_current(self) -> None:
        """Show currently selected LLM model"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[cyan]Loading current LLM selection...[/cyan]")

        try:
            result = self.api.get_current_llm()

            if not result.get("success"):
                self.print_error("Failed to load current LLM")
                return

            data = result.get("data", {})

            self.console.print("[bold cyan]Currently Selected LLM[/bold cyan]\n")

            from cli.utils.table_formatter import format_key_value_table

            llm_info = {
                "Provider": data.get("provider", "Unknown"),
                "Model": data.get("model", "Unknown"),
                "Description": data.get("description", "N/A"),
                "Context Window": data.get("context_window", "N/A"),
                "Cost per 1K tokens": f"${data.get('cost_per_1k_tokens', 'N/A')}",
                "Selected At": data.get("selected_at", "N/A"),
            }

            table = format_key_value_table(llm_info)
            self.console.print(table)

            # Show info about switching
            self.console.print("\n[dim]Use [bold]/llm select[/bold] to change the model[/dim]")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def select_model(self) -> None:
        """Select LLM provider and model"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[bold cyan]Select LLM Provider and Model[/bold cyan]\n")

        try:
            # Get available models
            result = self.api.list_available_llms()

            if not result.get("success"):
                self.print_error("Failed to load models")
                return

            data = result.get("data", {})
            providers = data.get("providers", {})

            if not providers:
                self.print_error("No LLM providers configured")
                return

            # Step 1: Select provider
            provider_options = list(providers.keys())
            provider = prompts.prompt_choice(
                self.console,
                "Select provider",
                provider_options,
                default=provider_options[0]
            )

            # Step 2: Select model from provider
            provider_models = providers.get(provider, [])
            model_names = [m.get("name", "Unknown") for m in provider_models]

            if not model_names:
                self.print_error(f"No models available for {provider}")
                return

            model = prompts.prompt_choice(
                self.console,
                "Select model",
                model_names,
                default=model_names[0]
            )

            # Get selected model details
            selected_model = next((m for m in provider_models if m.get("name") == model), None)

            if selected_model:
                # Show details before confirming
                self.console.print(f"\n[bold cyan]{provider.upper()} - {model}[/bold cyan]")
                self.console.print(f"Description: {selected_model.get('description', 'N/A')}")
                self.console.print(f"Context Window: {selected_model.get('context_window', 'N/A')}")
                self.console.print(f"Cost: ${selected_model.get('cost_per_1k_tokens', 'N/A')}/1K tokens\n")

                if not prompts.prompt_confirm(
                    self.console,
                    f"Use {provider} {model}?",
                    default=True
                ):
                    self.console.print("[yellow]Cancelled[/yellow]")
                    return

                # Submit selection
                select_result = self.api.select_llm(provider, model)

                if select_result.get("success"):
                    self.print_success(f"LLM updated: {provider} {model}")
                else:
                    error = select_result.get("error") or "Unknown error"
                    self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def show_usage(self) -> None:
        """Show LLM usage statistics"""
        user = self.ensure_authenticated()
        if not user:
            return

        # Get period
        period = prompts.prompt_choice(
            self.console,
            "Time period",
            ["today", "week", "month", "year"],
            default="month"
        )

        self.console.print(f"[cyan]Loading LLM usage for {period}...[/cyan]")

        try:
            result = self.api.get_llm_usage(period=period)

            if not result.get("success"):
                self.print_error("Failed to load usage data")
                return

            data = result.get("data", {})

            self.console.print(f"[bold cyan]LLM Usage - {period.upper()}[/bold cyan]\n")

            # Overall stats
            overall = data.get("overall", {})
            self.console.print("[bold]Overall Usage:[/bold]")
            self.console.print(f"  Total tokens: {overall.get('total_tokens', 0):,}")
            self.console.print(f"  Input tokens: {overall.get('input_tokens', 0):,}")
            self.console.print(f"  Output tokens: {overall.get('output_tokens', 0):,}")
            self.console.print(f"  Total cost: ${overall.get('total_cost', 0):.2f}\n")

            # Per-model stats
            by_model = data.get("by_model", {})
            if by_model:
                self.console.print("[bold]Usage by Model:[/bold]")
                for model, stats in by_model.items():
                    self.console.print(f"  {model}:")
                    self.console.print(f"    Tokens: {stats.get('tokens', 0):,}")
                    self.console.print(f"    Calls: {stats.get('calls', 0)}")
                    self.console.print(f"    Cost: ${stats.get('cost', 0):.2f}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def show_costs(self) -> None:
        """Show LLM cost estimates"""
        self.console.print("[cyan]Loading LLM cost information...[/cyan]")

        try:
            result = self.api.get_llm_costs()

            if not result.get("success"):
                self.print_error("Failed to load cost data")
                return

            data = result.get("data", {})

            self.console.print("[bold cyan]LLM Pricing[/bold cyan]\n")

            providers = data.get("providers", {})

            for provider, models in providers.items():
                self.console.print(f"[bold yellow]{provider.upper()}[/bold yellow]")

                for model in models:
                    name = model.get("name", "Unknown")
                    input_cost = model.get("input_cost_per_1k", 0)
                    output_cost = model.get("output_cost_per_1k", 0)

                    self.console.print(f"  [cyan]{name}[/cyan]")
                    self.console.print(f"    Input: ${input_cost:.4f}/1K tokens")
                    self.console.print(f"    Output: ${output_cost:.4f}/1K tokens")
                    self.console.print(f"    Avg: ${(input_cost + output_cost) / 2:.4f}/1K tokens")

                self.console.print()

            # Show comparison
            comparison = data.get("comparison", {})
            if comparison:
                self.console.print("[bold]Cost Comparison (1M tokens):[/bold]")
                for provider, cost in comparison.items():
                    self.console.print(f"  {provider}: ${cost:.2f}")

        except Exception as e:
            self.print_error(f"Error: {e}")
