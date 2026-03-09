"""Tests for the Click CLI."""

from click.testing import CliRunner

from dfireballz.main import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output


def test_cli_catalog():
    runner = CliRunner()
    result = runner.invoke(cli, ["catalog"])
    assert result.exit_code == 0
    assert "volatility3" in result.output


def test_cli_templates_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["templates", "list"])
    assert result.exit_code == 0
    assert "malware-analysis" in result.output


def test_cli_templates_show():
    runner = CliRunner()
    result = runner.invoke(cli, ["templates", "show", "malware-analysis"])
    assert result.exit_code == 0
    assert "Malware" in result.output


def test_cli_templates_show_unknown():
    runner = CliRunner()
    result = runner.invoke(cli, ["templates", "show", "nonexistent"])
    assert result.exit_code == 1
