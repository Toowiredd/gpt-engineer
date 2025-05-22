"""Utilities to generate a simple microservice from a prompt."""
from __future__ import annotations

from pathlib import Path


def _parse_prompt(prompt: str) -> tuple[str, str, int]:
    """Extract an endpoint path, message and port from the prompt.

    If no details are found defaults are returned.
    """
    endpoint = "/"
    message = "Hello from GPT Engineer!"
    port = 80

    # very naive parsing for `/path`, quoted message after 'return', and port number
    tokens = prompt.replace(":", " ").replace(",", " ").split()
    for w in tokens:
        if w.startswith("/"):
            endpoint = w
            break

    if "return" in prompt:
        after = prompt.split("return", 1)[1]
        for quote in ['"', "'"]:
            if quote in after:
                message = after.split(quote)[1]
                break

    for i, token in enumerate(tokens):
        if token.lower() == "port" and i + 1 < len(tokens):
            num = tokens[i + 1].rstrip(".")
            if num.isdigit():
                port = int(num)
                break

    return endpoint, message, port


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

    endpoint, message, port = _parse_prompt(prompt)

    app_py = f"""from flask import Flask, jsonify

app = Flask(__name__)

@app.route('{endpoint}')
def endpoint():
    return jsonify(message="{message}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port={port})
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
