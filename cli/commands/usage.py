"""Usage analytics commands"""

import typer
from typing import Optional
from rich.console import Console

from ..api_client import APIClient
from ..utils import (
    print_success,
    print_error,
    print_warning,
    print_info,
    create_data_table,
    format_cost,
    format_tokens,
    format_duration,
)

app = typer.Typer(help="Usage analytics")
console = Console()


@app.command()
def summary(
    period: str = typer.Option("week", help="Time period (today, week, month, all)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Overall usage summary"""

    try:
        client = APIClient()

        # Get usage data
        # Note: Current API doesn't have period filtering, so we get all and note it
        usage = client.get_usage()

        if json_output:
            import json
            print(json.dumps(usage, indent=2, default=str))
            return

        # Display summary (placeholder - actual implementation would aggregate data)
        print_warning(f"Usage summary endpoint not yet implemented in API")
        print_info("Using basic usage data...")

        print()
        console.print(f"Usage Summary (Period: {period})", style="bold cyan")
        console.print("━" * 60)

        # Show basic info
        console.print(f"\nNote: Full analytics coming in future API version")
        console.print(f"Use 'claude-api usage by-project' for current data")

    except Exception as e:
        print_error(f"Failed to get usage summary: {str(e)}")
        raise typer.Exit(1)


@app.command()
def by_project(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Usage breakdown by project"""

    try:
        client = APIClient()

        # Get all keys and their projects
        print_info("Aggregating usage by project...")

        # Placeholder - would need API endpoint for this
        print_warning("Project-level analytics endpoint not yet implemented in API")
        print_info("Run 'claude-api keys list' to see projects")

    except Exception as e:
        print_error(f"Failed to get project usage: {str(e)}")
        raise typer.Exit(1)


@app.command()
def by_model(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Usage breakdown by model"""

    try:
        print_warning("Model-level analytics endpoint not yet implemented in API")
        print_info("This feature requires API enhancement")

    except Exception as e:
        print_error(f"Failed to get model usage: {str(e)}")
        raise typer.Exit(1)


@app.command()
def costs(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Cost breakdown"""

    try:
        print_warning("Cost analytics endpoint not yet implemented in API")
        print_info("This feature requires API enhancement")

    except Exception as e:
        print_error(f"Failed to get costs: {str(e)}")
        raise typer.Exit(1)


@app.command()
def export(
    format: str = typer.Option("csv", help="Export format (csv, json)"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export usage data"""

    try:
        print_warning("Usage export endpoint not yet implemented in API")
        print_info("This feature requires API enhancement")

    except Exception as e:
        print_error(f"Failed to export usage: {str(e)}")
        raise typer.Exit(1)
