"""Basic CLI integration tests for cvlint."""

import pytest
import json
from typer.testing import CliRunner
from pathlib import Path
from src.cvlint.cli import app

runner = CliRunner()


class TestBasicCLI:
    """Basic CLI functionality tests."""

    def test_help_command(self):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CV Linting Tool" in result.stdout
        assert "check" in result.stdout
        assert "list-criteria" in result.stdout
        assert "config" in result.stdout

    def test_list_criteria_command(self):
        """Test that list-criteria command works."""
        result = runner.invoke(app, ["list-criteria"])
        assert result.exit_code == 0
        assert "Available Validation Criteria" in result.stdout
        assert "PDF File Exists" in result.stdout
        assert "Single Page Limit" in result.stdout
        assert "Total Weight:" in result.stdout

    def test_config_command(self):
        """Test that config command works."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Default Configuration Values" in result.stdout
        assert "max_pages" in result.stdout
        assert "min_font" in result.stdout
        assert "max_font" in result.stdout


class TestCheckCommand:
    """Basic check command tests."""

    def test_check_nonexistent_file(self):
        """Test check command with non-existent file."""
        result = runner.invoke(app, ["check", "nonexistent.pdf"])
        assert result.exit_code == 1
        assert "Error: PDF file not found" in result.stdout

    # FIXME: this test is fragile, JSON output should be fixed.
    def test_check_valid_pdf_json_output(self, valid_pdf):
        """Test check command with valid PDF and JSON output."""
        result = runner.invoke(app, ["check", str(valid_pdf), "--output", "json"])
        assert result.exit_code in [0, 1]  # May pass or fail depending on PDF content

        # Extract JSON from output (may have progress text before it)
        lines = result.stdout.strip().split("\n")
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        assert json_start >= 0, "No JSON found in output"
        json_text = "\n".join(lines[json_start:])

        # Parse JSON output
        output_data = json.loads(json_text)
        assert "pdf_path" in output_data
        assert "score" in output_data
        assert "passed" in output_data
        assert "total" in output_data
        assert "results" in output_data
        assert isinstance(output_data["results"], list)

    def test_check_valid_pdf_summary_output(self, valid_pdf):
        """Test check command with valid PDF and summary output."""
        result = runner.invoke(app, ["check", str(valid_pdf), "--output", "summary"])
        assert result.exit_code in [0, 1]  # May pass or fail depending on PDF content
        assert "CV Validation Results" in result.stdout
        assert "Score:" in result.stdout
        assert "Passed:" in result.stdout

    def test_check_with_specific_criteria(self, valid_pdf):
        """Test check command with specific criteria."""
        result = runner.invoke(
            app, ["check", str(valid_pdf), "--criteria", "PDF File Exists"]
        )
        assert result.exit_code == 0  # Should pass since file exists
        assert "PDF File Exists" in result.stdout

    def test_check_invalid_criteria(self, valid_pdf):
        """Test check command with invalid criteria name."""
        result = runner.invoke(
            app, ["check", str(valid_pdf), "--criteria", "NonExistentCriteria"]
        )
        assert result.exit_code == 1
        assert "No matching criteria found" in result.stdout

    def test_check_invalid_passing_score(self, valid_pdf):
        """Test check command with invalid passing score."""
        result = runner.invoke(app, ["check", str(valid_pdf), "--passing-score", "150"])
        assert result.exit_code == 1
        assert "Passing score must be between 0 and 100" in result.stdout

    def test_check_with_cli_options(self, valid_pdf):
        """Test check command with various CLI options."""
        result = runner.invoke(
            app,
            [
                "check",
                str(valid_pdf),
                "--max-pages",
                "2",
                "--min-font",
                "10",
                "--max-font",
                "20",
                "--max-file-size",
                "1000",
            ],
        )
        assert result.exit_code in [0, 1]  # May pass or fail depending on PDF content
        # Just verify it runs without crashing
