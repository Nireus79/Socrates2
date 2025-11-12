"""Tests for CLI module."""

import pytest
from click.testing import CliRunner

from ..cli.main import cli
from ..domains.registry import register_all_domains


@pytest.fixture(scope="session", autouse=True)
def register_domains():
    """Register all domains before running tests."""
    try:
        register_all_domains()
    except ValueError:
        # Domains already registered
        pass


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestDomainCommands:
    """Test domain-related CLI commands."""

    def test_domain_list(self, cli_runner):
        """Test listing domains."""
        result = cli_runner.invoke(cli, ["domain", "list"])

        assert result.exit_code == 0
        assert "programming" in result.output
        assert "testing" in result.output
        assert "architecture" in result.output

    def test_domain_info(self, cli_runner):
        """Test getting domain info."""
        result = cli_runner.invoke(cli, ["domain", "info", "programming"])

        assert result.exit_code == 0
        assert "programming" in result.output
        assert "Questions:" in result.output
        assert "Export Formats:" in result.output

    def test_domain_info_nonexistent(self, cli_runner):
        """Test getting info for non-existent domain."""
        result = cli_runner.invoke(cli, ["domain", "info", "nonexistent"])

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_domain_questions(self, cli_runner):
        """Test listing domain questions."""
        result = cli_runner.invoke(cli, ["domain", "questions", "programming"])

        assert result.exit_code == 0
        assert "Programming" in result.output
        assert "Questions" in result.output


class TestWorkflowCommands:
    """Test workflow-related CLI commands."""

    def test_workflow_create(self, cli_runner):
        """Test creating a workflow."""
        result = cli_runner.invoke(cli, ["workflow", "create", "test_wf_001"])

        assert result.exit_code == 0
        assert "Created workflow" in result.output

    def test_workflow_create_with_domain(self, cli_runner):
        """Test creating workflow with domain."""
        result = cli_runner.invoke(cli, ["workflow", "create", "test_wf_002", "-d", "programming"])

        assert result.exit_code == 0
        assert "Created workflow" in result.output
        assert "Added domain" in result.output

    def test_workflow_list(self, cli_runner):
        """Test listing workflows."""
        # Create a workflow first
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_list"])

        result = cli_runner.invoke(cli, ["workflow", "list"])

        assert result.exit_code == 0
        assert "Workflows" in result.output

    def test_workflow_show(self, cli_runner):
        """Test showing workflow details."""
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_show"])

        result = cli_runner.invoke(cli, ["workflow", "show", "test_wf_show"])

        assert result.exit_code == 0
        assert "Workflow: test_wf_show" in result.output

    def test_workflow_add_domain(self, cli_runner):
        """Test adding domain to workflow."""
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_add"])

        result = cli_runner.invoke(cli, ["workflow", "add", "test_wf_add", "programming"])

        assert result.exit_code == 0
        assert "Added domain" in result.output

    def test_workflow_validate(self, cli_runner):
        """Test workflow validation."""
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_validate", "-d", "programming"])

        result = cli_runner.invoke(cli, ["workflow", "validate", "test_wf_validate"])

        assert result.exit_code == 0
        assert "Validation Result" in result.output

    def test_workflow_export(self, cli_runner):
        """Test exporting workflow."""
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_export", "-d", "programming"])

        result = cli_runner.invoke(cli, ["workflow", "export", "test_wf_export"])

        assert result.exit_code == 0
        assert "workflow_id" in result.output
        assert "test_wf_export" in result.output

    def test_workflow_delete(self, cli_runner):
        """Test deleting workflow."""
        cli_runner.invoke(cli, ["workflow", "create", "test_wf_delete"])

        result = cli_runner.invoke(cli, ["workflow", "delete", "test_wf_delete"], input="y\n")

        assert result.exit_code == 0
        assert "Deleted workflow" in result.output


class TestAnalyticsCommands:
    """Test analytics-related CLI commands."""

    def test_analytics_report(self, cli_runner):
        """Test analytics report."""
        result = cli_runner.invoke(cli, ["analytics", "report"])

        assert result.exit_code == 0
        assert "Analytics Report" in result.output

    def test_analytics_quality(self, cli_runner):
        """Test quality summary."""
        result = cli_runner.invoke(cli, ["analytics", "quality"])

        assert result.exit_code == 0
        assert "Quality Summary" in result.output

    def test_analytics_domains(self, cli_runner):
        """Test most used domains."""
        result = cli_runner.invoke(cli, ["analytics", "domains"])

        assert result.exit_code == 0

    def test_analytics_export(self, cli_runner):
        """Test exporting analytics."""
        result = cli_runner.invoke(cli, ["analytics", "export"])

        assert result.exit_code == 0
        assert "export_timestamp" in result.output


class TestVersionAndHelp:
    """Test version and help commands."""

    def test_version(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, cli_runner):
        """Test help command."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Socrates" in result.output

    def test_domain_help(self, cli_runner):
        """Test domain subcommand help."""
        result = cli_runner.invoke(cli, ["domain", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "info" in result.output

    def test_workflow_help(self, cli_runner):
        """Test workflow subcommand help."""
        result = cli_runner.invoke(cli, ["workflow", "--help"])

        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output

    def test_analytics_help(self, cli_runner):
        """Test analytics subcommand help."""
        result = cli_runner.invoke(cli, ["analytics", "--help"])

        assert result.exit_code == 0
        assert "report" in result.output
        assert "quality" in result.output
