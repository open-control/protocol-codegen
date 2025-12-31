"""
Tests for CLI module.

Validates CLI commands and argument parsing.
"""

from __future__ import annotations

from click.testing import CliRunner

from protocol_codegen.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self) -> None:
        """CLI should show help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Protocol CodeGen" in result.output

    def test_cli_version(self) -> None:
        """CLI should show version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_list_methods(self) -> None:
        """list-methods should show available methods."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list-methods"])

        assert result.exit_code == 0
        assert "sysex" in result.output

    def test_list_generators(self) -> None:
        """list-generators should show available generators."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list-generators"])

        assert result.exit_code == 0
        assert "C++" in result.output
        assert "Java" in result.output

    def test_generate_missing_options(self) -> None:
        """generate without required options should fail."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_validate_command_exists(self) -> None:
        """validate command should exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--help"])

        assert result.exit_code == 0
        assert "validate" in result.output.lower() or "Validate" in result.output
