"""Document and knowledge base management commands.

/document upload - Upload file to knowledge base
/document list - List project documents
/document search - Semantic search documents
/document delete - Delete document
"""

from typing import List
from pathlib import Path
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class DocumentCommandHandler(CommandHandler):
    """Handler for document management commands"""

    command_name = "document"
    description = "Documents: upload, list, search, delete"
    help_text = """
[bold cyan]Document Commands:[/bold cyan]
  [yellow]/document upload <file>[/yellow]   Upload file to knowledge base
  [yellow]/document list[/yellow]            List project documents
  [yellow]/document search <query>[/yellow]  Semantic search documents
  [yellow]/document delete <id>[/yellow]     Delete document
"""

    def handle(self, args: List[str]) -> None:
        """Route document commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "upload":
            self.upload(args[1:])
        elif subcommand == "list":
            self.list()
        elif subcommand == "search":
            self.search(args[1:])
        elif subcommand == "delete":
            self.delete(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def upload(self, args: List[str]) -> None:
        """Upload document to knowledge base"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /document upload <file_path>[/yellow]")
            return

        file_path = Path(args[0])

        if not file_path.exists():
            self.print_error(f"File not found: {file_path}")
            return

        try:
            self.console.print(f"[cyan]Uploading {file_path.name}...[/cyan]")

            with open(file_path, "rb") as f:
                result = self.api.upload_document(project.get("id"), f)

            if result.get("success"):
                self.print_success(f"Document uploaded: {file_path.name}")
                self.console.print(f"[cyan]Document ID: {result.get('document_id')}[/cyan]")
                self.console.print(f"[cyan]Chunks: {result.get('chunks')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def list(self) -> None:
        """List project documents"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading documents...[/cyan]")

        try:
            result = self.api.list_documents(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load documents")
                return

            documents = result.get("data", {}).get("documents", [])

            if not documents:
                self.console.print("[yellow]No documents in this project[/yellow]")
                return

            self.console.print("[bold cyan]Project Documents[/bold cyan]\n")

            for i, doc in enumerate(documents, 1):
                name = doc.get("filename", "Unknown")
                size = doc.get("file_size", 0)
                chunks = doc.get("chunks_count", 0)
                created = doc.get("uploaded_at", "N/A")

                size_mb = size / (1024 * 1024)
                self.console.print(f"[yellow]{i}.[/yellow] {name}")
                self.console.print(f"   Size: {size_mb:.1f}MB | Chunks: {chunks} | Uploaded: {created}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def search(self, args: List[str]) -> None:
        """Semantic search documents"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            query = prompts.prompt_text(self.console, "Search query")
        else:
            query = " ".join(args)

        try:
            self.console.print("[cyan]Searching documents...[/cyan]")

            result = self.api.semantic_search(project.get("id"), query)

            if not result.get("success"):
                self.print_error("Search failed")
                return

            results = result.get("data", {}).get("results", [])

            if not results:
                self.console.print("[yellow]No results found[/yellow]")
                return

            self.console.print(f"\n[bold cyan]Search Results for: {query}[/bold cyan]\n")

            for i, match in enumerate(results, 1):
                relevance = match.get("relevance_score", 0)
                content = match.get("content", "")[:100]

                self.console.print(f"[yellow]{i}.[/yellow] [bold]Relevance: {relevance:.2f}[/bold]")
                self.console.print(f"   {content}...\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def delete(self, args: List[str]) -> None:
        """Delete document"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /document delete <document_id>[/yellow]")
            return

        doc_id = args[0]

        if not prompts.prompt_confirm(
            self.console,
            "Delete document?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            result = self.api.delete_document(doc_id)

            if result.get("success"):
                self.print_success("Document deleted")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
