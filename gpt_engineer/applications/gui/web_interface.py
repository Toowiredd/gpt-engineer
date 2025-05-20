"""A minimal Flask web interface for gpt-engineer."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, redirect, render_template_string, request, url_for

from gpt_engineer.applications.cli.cli_agent import CliAgent
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.file_store import FileStore
from gpt_engineer.core.default.paths import memory_path
from gpt_engineer.core.prompt import Prompt

app = Flask(__name__)

PROJECT_DIR = Path("projects/example")
MEMORY = DiskMemory(memory_path(PROJECT_DIR))
EXEC_ENV = DiskExecutionEnv()
STORE = FileStore(PROJECT_DIR)
AGENT = CliAgent.with_default_config(MEMORY, EXEC_ENV)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    if request.method == "POST":
        prompt_text = request.form.get("prompt", "")
        if prompt_text:
            files = AGENT.init(Prompt(prompt_text))
            STORE.push(files)
            return redirect(url_for("done"))
    return render_template_string(
        """
        <form method='post'>
            <textarea name='prompt' rows='10' cols='60'></textarea><br>
            <input type='submit' value='Generate'>
        </form>
        """
    )


@app.route("/done")
def done():
    return "Generation complete"


def run(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Run the Flask development server."""
    app.run(host=host, port=port)
