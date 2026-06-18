"""CLI interface for LangGraph CSV Analyst using Typer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langgraph_csv_analyst import __version__
from langgraph_csv_analyst.csv_parser import get_profile, get_summary, load_csv
from langgraph_csv_analyst.graph import run_analysis

app = typer.Typer(
    name="langgraph-analyst",
    help="LangGraph CSV Analyst - Multi-agent CSV analysis tool",
    add_completion=False,
)

console = Console()


@app.command()
def analyze(
    csv_path: str = typer.Argument(..., help="Path to the CSV file to analyze"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output HTML report path (default: <csv_name>_report.html)"
    ),
) -> None:
    """Run the full analysis pipeline on a CSV file and generate an HTML report."""
    csv_file = Path(csv_path)
    if not csv_file.exists():
        console.print(f"[red]Error: File not found: {csv_path}[/red]")
        raise typer.Exit(code=1)

    if not csv_file.suffix.lower() == ".csv":
        console.print(f"[red]Error: File must be a CSV: {csv_path}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel(f"Analyzing: [bold]{csv_path}[/bold]", title="LangGraph CSV Analyst"))

    with console.status("[bold green]Running analysis pipeline..."):
        result = run_analysis(str(csv_file))

    errors = result.get("errors", [])
    if errors:
        console.print("[bold red]Errors encountered:[/bold red]")
        for error in errors:
            console.print(f"  [red]- {error}[/red]")

    report = result.get("report", "")
    if report:
        output_path = output or str(csv_file.with_suffix(".html")).replace(
            csv_file.stem, f"{csv_file.stem}_report"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        console.print(f"\n[bold green]Report saved to: {output_path}[/bold green]")
    else:
        console.print("[bold red]No report was generated.[/bold red]")

    profile = result.get("profile", {})
    if profile:
        _display_profile_summary(profile)


@app.command()
def profile(
    csv_path: str = typer.Argument(..., help="Path to the CSV file to profile"),
) -> None:
    """Quick data profile of a CSV file."""
    csv_file = Path(csv_path)
    if not csv_file.exists():
        console.print(f"[red]Error: File not found: {csv_path}[/red]")
        raise typer.Exit(code=1)

    with console.status("[bold green]Loading CSV..."):
        df = load_csv(csv_path)

    summary = get_summary(df)
    prof = get_profile(df)

    # Display summary
    console.print(Panel("Data Summary", style="bold blue"))
    console.print(f"  Rows: [bold]{summary['shape']['rows']:,}[/bold]")
    console.print(f"  Columns: [bold]{summary['shape']['columns']}[/bold]")
    console.print(f"  Memory: [bold]{summary['memory_usage_mb']} MB[/bold]")
    console.print(f"  Null values: [bold]{summary['null_total']:,}[/bold]")
    console.print(f"  Duplicate rows: [bold]{summary['duplicate_rows']:,}[/bold]")

    # Display column table
    _display_profile_summary(prof)


def _display_profile_summary(profile_data: dict) -> None:
    """Display a profile summary using Rich tables."""
    table = Table(title="Column Profile", show_lines=True)
    table.add_column("Column", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Nulls", style="yellow")
    table.add_column("Unique", style="magenta")
    table.add_column("Details", style="white")

    for col in profile_data.get("columns", []):
        stats = col.get("stats", {})
        if "mean" in stats:
            details = f"mean={stats.get('mean')}, std={stats.get('std')}"
        else:
            top_vals = stats.get("top_values", {})
            top_str = ", ".join(f"{k}({v})" for k, v in list(top_vals.items())[:3])
            details = top_str or "N/A"

        table.add_row(
            col["name"],
            col["dtype"],
            f"{col['null_count']} ({col['null_pct']}%)",
            str(col["unique_count"]),
            details,
        )

    console.print(table)


@app.command()
def version() -> None:
    """Show the version."""
    console.print(f"LangGraph CSV Analyst v{__version__}")


if __name__ == "__main__":
    app()
