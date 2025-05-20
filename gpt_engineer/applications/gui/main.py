"""GUI entry point for GPT Engineer."""

from pathlib import Path

import typer

from gpt_engineer.applications.cli import main as cli_main

app = typer.Typer()


@app.command()
def run(project_path: Path = typer.Argument(..., help="Directory to store generated files")):
    """Run the GUI and save project files in ``project_path``."""
    cli_main.main(str(project_path))


if __name__ == "__main__":
    app()
