import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import json

from .main import create_criteria_list, Criterion, ValidationConfig

app = typer.Typer(
    help="CV Linting Tool - Validate PDF resumes against quality criteria"
)
console = Console()


@app.command()
def check(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file to validate"),
    criteria: Optional[List[str]] = typer.Option(
        None, "--criteria", "-c", help="Specific criteria to run (comma-separated)"
    ),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format: table, json, summary"
    ),
    passing_score: float = typer.Option(
        80.0,
        "--passing-score",
        help="Minimum score required for CLI to succeed (0-100)",
    ),
    max_pages: int = typer.Option(1, "--max-pages", help="Maximum allowed pages"),
    min_font: int = typer.Option(8, "--min-font", help="Minimum font size in points"),
    max_font: int = typer.Option(21, "--max-font", help="Maximum font size in points"),
    max_file_size: float = typer.Option(
        500, "--max-file-size", help="Maximum file size in KB"
    ),
    no_https: bool = typer.Option(
        False, "--no-https", help="Disable HTTPS requirement for links"
    ),
    allow_images: bool = typer.Option(
        False, "--allow-images", help="Allow embedded images"
    ),
    allow_colors: bool = typer.Option(
        False, "--allow-colors", help="Allow non-grayscale colors"
    ),
    no_white_bg: bool = typer.Option(
        False, "--no-white-bg", help="Don't require white background"
    ),
    custom_words: Optional[str] = typer.Option(
        None, "--custom-words", help="Custom words file (one word per line)"
    ),
):
    """Validate a PDF resume against quality criteria."""

    # Validate passing score range
    if not 0 <= passing_score <= 100:
        rprint(
            f"[red]Error: Passing score must be between 0 and 100, got {passing_score}[/red]"
        )
        raise typer.Exit(1)

    # Validate PDF exists
    if not pdf_path.exists():
        rprint(f"[red]Error: PDF file not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    # Load custom words if provided
    custom_words_list = []
    if custom_words:
        custom_words_path = Path(custom_words)
        if custom_words_path.exists():
            custom_words_list = custom_words_path.read_text().strip().split("\n")
        else:
            rprint(
                f"[yellow]Warning: Custom words file not found: {custom_words_path}[/yellow]"
            )

    # Create validation configuration
    config = ValidationConfig(
        pdf_path=pdf_path,
        max_pages=max_pages,
        max_file_size_kb=max_file_size,
        min_font=min_font,
        max_font=max_font,
        enforce_https=not no_https,
        no_images=not allow_images,
        background_white=not no_white_bg,
        grayscale_colors=not allow_colors,
        custom_words=custom_words_list,
    )

    # Get all criteria
    all_criteria = create_criteria_list(config)

    # Filter criteria if specific ones requested
    if criteria:
        criteria_names = [c.strip() for c in criteria]
        filtered_criteria = [c for c in all_criteria if c.name in criteria_names]
        if not filtered_criteria:
            rprint(f"[red]Error: No matching criteria found. Available criteria:[/red]")
            for criterion in all_criteria:
                rprint(f"  - {criterion.name}")
            raise typer.Exit(1)
        all_criteria = filtered_criteria

    # Run validation
    results = []
    total_weight = sum(c.weight for c in all_criteria)
    passed_weight = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running validation...", total=len(all_criteria))

        for criterion in all_criteria:
            progress.update(task, description=f"Checking: {criterion.name}")

            try:
                passed = criterion.check_func()
                if passed:
                    passed_weight += criterion.weight
                results.append(
                    {
                        "name": criterion.name,
                        "description": criterion.description,
                        "weight": criterion.weight,
                        "passed": passed,
                        "error": None,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "name": criterion.name,
                        "description": criterion.description,
                        "weight": criterion.weight,
                        "passed": False,
                        "error": str(e),
                    }
                )

            progress.advance(task)

    # Calculate score
    score = (passed_weight / total_weight) * 100 if total_weight > 0 else 0
    passed_count = sum(1 for r in results if r["passed"])

    # Output results
    if output == "json":
        output_data = {
            "pdf_path": str(pdf_path),
            "score": round(score, 2),
            "passed": passed_count,
            "total": len(results),
            "results": results,
        }
        print(json.dumps(output_data, indent=2))

    elif output == "summary":
        rprint(f"\n[bold]CV Validation Results for: {pdf_path}[/bold]")
        score_color = (
            "green"
            if score >= passing_score
            else "yellow" if score >= passing_score * 0.75 else "red"
        )
        rprint(
            f"Score: [{score_color}]{score:.1f}%[/] (Required: {passing_score:.1f}%)"
        )
        rprint(f"Passed: {passed_count}/{len(results)} criteria")

        if score >= passing_score:
            rprint(f"[green]PASSED - Score meets minimum requirement[/green]")
        else:
            rprint(
                f"[red]FAILED - Score below minimum requirement of {passing_score:.1f}%[/red]"
            )

        failed_results = [r for r in results if not r["passed"]]
        if failed_results:
            rprint(f"\n[red]Failed Criteria:[/red]")
            for result in failed_results:
                rprint(f"  - {result['name']}")
                if result["error"]:
                    rprint(f"     Error: {result['error']}")

    else:  # table format (default)
        table = Table(title=f"CV Validation Results - {pdf_path}")
        table.add_column("Criterion", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Weight", justify="right")
        table.add_column("Description", style="dim")

        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            status_style = "green" if result["passed"] else "red"

            table.add_row(
                result["name"],
                f"[{status_style}]{status}[/]",
                f"{result['weight']:.1f}",
                result["description"],
            )

        console.print(table)

        # Summary panel
        score_color = (
            "green"
            if score >= passing_score
            else "yellow" if score >= passing_score * 0.75 else "red"
        )
        summary_text = f"Score: [{score_color}]{score:.1f}%[/] (Required: {passing_score:.1f}%) | Passed: {passed_count}/{len(results)} criteria"

        if score >= passing_score:
            panel_title = "Summary - PASSED"
            panel_style = "green"
        else:
            panel_title = "Summary - FAILED"
            panel_style = "red"

        console.print(Panel(summary_text, title=panel_title, border_style=panel_style))

    # Exit with error code if score is below passing score
    if score < passing_score:
        raise typer.Exit(1)


@app.command()
def list_criteria():
    """List all available validation criteria."""
    # Create a dummy config for listing criteria
    dummy_config = ValidationConfig(pdf_path=Path("dummy.pdf"))
    criteria = create_criteria_list(dummy_config)

    table = Table(title="Available Validation Criteria")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Weight", justify="right")
    table.add_column("Description", style="dim")

    total_weight = sum(c.weight for c in criteria)

    for criterion in criteria:
        table.add_row(criterion.name, f"{criterion.weight:.1f}", criterion.description)

    console.print(table)
    console.print(f"\n[bold]Total Weight: {total_weight:.1f} points[/bold]")


@app.command()
def config():
    """Show current configuration values."""
    # Create a default config to show default values
    default_config = ValidationConfig(pdf_path=Path("example.pdf"))

    table = Table(title="Default Configuration Values")
    table.add_column("Setting", style="cyan")
    table.add_column("Default Value", style="green")
    table.add_column("Description", style="dim")

    config_items = [
        ("max_pages", default_config.max_pages, "Maximum allowed pages"),
        ("min_font", default_config.min_font, "Minimum font size in points"),
        ("max_font", default_config.max_font, "Maximum font size in points"),
        ("enforce_https", default_config.enforce_https, "Require HTTPS for links"),
        (
            "max_file_size_kb",
            default_config.max_file_size_kb,
            "Maximum file size in KB",
        ),
        ("no_images", default_config.no_images, "Prohibit embedded images"),
        (
            "background_white",
            default_config.background_white,
            "Require white background",
        ),
        (
            "grayscale_colors",
            default_config.grayscale_colors,
            "Require grayscale colors only",
        ),
    ]

    for setting, value, description in config_items:
        table.add_row(setting, str(value), description)

    console.print(table)
    rprint(
        f"\n[dim]Note: These are default values. Use command-line options to override them.[/dim]"
    )


if __name__ == "__main__":
    app()
