"""Utilities to generate a simple microservice from a prompt."""
from __future__ import annotations

from pathlib import Path


def _parse_prompt(prompt: str) -> tuple[str, str]:
    """Extract an endpoint path and message from the prompt.

    If no path or message is found a default one is returned.
    """
    endpoint = "/"
    message = "Hello from GPT Engineer!"

    # very naive parsing for `/path` and quoted message after 'return'
    words = prompt.split()
    for w in words:
        if w.startswith("/"):
            endpoint = w
            break

    if "return" in prompt:
        after = prompt.split("return", 1)[1]
        for quote in ['"', "'"]:
            if quote in after:
                message = after.split(quote)[1]
                break
    return endpoint, message


def generate_microservice(project_path: Path | str, prompt: str) -> None:
    """Generate a small Flask microservice based on the prompt.

    Parameters
    ----------
    project_path : Path | str
        Directory where the service files will be written.
    prompt : str
        Natural language description of the service.
    """
    path = Path(project_path)
    path.mkdir(parents=True, exist_ok=True)

    endpoint, message = _parse_prompt(prompt)

    app_py = f"""from flask import Flask, jsonify

app = Flask(__name__)

@app.route('{endpoint}')
def endpoint():
    return jsonify(message="{message}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
"""
    (path / "app.py").write_text(app_py)
    (path / "requirements.txt").write_text("flask\n")

    dockerfile = """FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [\"python\", \"app.py\"]
"""
    (path / "Dockerfile").write_text(dockerfile)
