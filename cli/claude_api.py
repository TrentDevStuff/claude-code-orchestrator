#!/usr/bin/env python3
"""Claude Code API Service CLI - Main Entry Point"""

import typer
from typing import Optional
from rich.console import Console

from .config import config_manager
from .utils import print_error, print_success, print_info

app = typer.Typer(
    name="claude-api",
    help="Claude Code API Service CLI - Manage and monitor your API service",
    add_completion=True,
)

console = Console()


@app.command()
def version():
    """Show CLI version"""
    from . import __version__
    print(f"claude-api version {__version__}")


@app.command()
def config_show():
    """Show current configuration"""
    try:
        config = config_manager.load()

        print_info(f"Configuration loaded from: {config_manager.config_file}")
        print()

        console.print("Service Configuration:", style="bold cyan")
        console.print(f"  Directory: {config.service.directory}")
        console.print(f"  Port: {config.service.port}")
        console.print(f"  Host: {config.service.host}")
        console.print(f"  Auto Start: {config.service.auto_start}")
        print()

        console.print("CLI Configuration:", style="bold cyan")
        console.print(f"  Default Output: {config.cli.default_output}")
        console.print(f"  Color: {config.cli.color}")
        console.print(f"  Verbose: {config.cli.verbose}")

        print()
        print_success(f"Service URL: {config_manager.get_service_url()}")

    except Exception as e:
        print_error(f"Failed to load configuration: {str(e)}")
        raise typer.Exit(1)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """
    Claude Code API Service CLI

    Manage, monitor, and test your Claude Code API Service.
    """
    if verbose:
        config = config_manager.load()
        config.cli.verbose = True


if __name__ == "__main__":
    app()
