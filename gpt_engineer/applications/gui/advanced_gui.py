from __future__ import annotations

# ruff: noqa: E402

"""A simple Flask-based GUI exposing advanced options."""

from pathlib import Path
from threading import Thread
from typing import List

try:
    from flask import Flask, jsonify, render_template_string, request
except Exception:  # pragma: no cover - optional dependency
    Flask = None  # type: ignore

from gpt_engineer.applications.cli.cli_agent import CliAgent
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.file_store import FileStore
from gpt_engineer.core.default.paths import memory_path
from gpt_engineer.core.prompt import Prompt

HELP_TEXT = """\
* **Model**: Which language model to use for generation.
* **Temperature**: Controls randomness of the model output.
* **Generate Microservice**: Creates a Flask microservice from your prompt.
* **Self Heal**: Attempts to automatically repair generated code.
"""

TEMPLATE = """
<!doctype html>
<title>GPT Engineer Advanced GUI</title>
<h1>GPT Engineer Advanced GUI</h1>
<form method='post'>
  <textarea name='prompt' rows='10' cols='60' placeholder='Enter prompt here'></textarea><br>
  Model: <input name='model'><br>
  Temperature: <input type='number' step='0.1' name='temperature' value='0.1'><br>
  <label><input type='checkbox' name='microservice'>Generate Microservice</label><br>
  <label><input type='checkbox' name='self_heal'>Enable Self Heal</label><br>
  <input id='run-button' type='submit' value='Run'>
</form>
<div>Status: <span id='status'>Idle</span></div>
<h2>Help</h2>
<pre>{{ help_text }}</pre>
<h2>Logs</h2>
<pre id='logs'></pre>
<script>
function fetchLogs() {
  fetch('/logs').then(r => r.json()).then(d => {
    document.getElementById('logs').textContent = d.logs.join('\n');
  });
}
function fetchStatus() {
  fetch('/status').then(r => r.json()).then(d => {
    document.getElementById('run-button').disabled = d.running;
    document.getElementById('status').textContent = d.running ? 'Running' : 'Idle';
  });
}
setInterval(() => { fetchLogs(); fetchStatus(); }, 1000);
fetchLogs();
fetchStatus();
</script>
"""


class AdvancedGUI:
    """Encapsulates the Flask application and agent."""

    def __init__(self, project_path: Path) -> None:
        if Flask is None:
            raise RuntimeError("Flask is required for the advanced GUI")
        self.project_path = Path(project_path)
        self.memory = DiskMemory(memory_path(self.project_path))
        self.execution_env = DiskExecutionEnv()
        self.store = FileStore(self.project_path)
        self.agent = CliAgent.with_default_config(self.memory, self.execution_env)
        self.logs: List[str] = []
        self.running = False
        self.agent.set_update_callback(self._log)
        self.app = Flask(__name__)
        self._setup_routes()

    def _log(self, message: str) -> None:
        self.logs.append(message)

    def _setup_routes(self) -> None:
        app = self.app

        @app.route("/", methods=["GET", "POST"])
        def index():
            if request.method == "POST":
                prompt_text = request.form.get("prompt", "")
                model = request.form.get("model")
                temperature = request.form.get("temperature", "0")
                microservice = request.form.get("microservice") is not None
                self_heal = request.form.get("self_heal") is not None
                self.logs.clear()
                self.running = True

                def task():
                    if model:
                        self.agent.config.model = model
                    if temperature:
                        try:
                            self.agent.config.temperature = float(temperature)
                        except ValueError:
                            pass
                    self.agent.self_heal_mode = self_heal
                    self.agent.microservice = microservice
                    try:
                        files = self.agent.init(Prompt(prompt_text))
                        self.store.push(files)
                    finally:
                        self.running = False

                Thread(target=task, daemon=True).start()
            return render_template_string(TEMPLATE, help_text=HELP_TEXT)

        @app.route("/logs")
        def logs():
            return jsonify(logs=self.logs)

        @app.route("/status")
        def status():
            return jsonify(running=self.running)

    def run(self, host: str = "127.0.0.1", port: int = 5000) -> None:
        self.app.run(host=host, port=port)


def create_app(project_path: Path | str = "projects/example") -> Flask:
    gui = AdvancedGUI(Path(project_path))
    return gui.app


def run(
    project_path: str = "projects/example", host: str = "127.0.0.1", port: int = 5000
) -> None:
    AdvancedGUI(Path(project_path)).run(host=host, port=port)
