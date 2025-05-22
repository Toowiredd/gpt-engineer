from pathlib import Path

from gpt_engineer.applications.service_generator.api_automator import generate_microservice


def test_generate_microservice(tmp_path: Path):
    prompt = "return 'pong' at /ping port 8080"
    generate_microservice(tmp_path, prompt)
    app_text = (tmp_path / "app.py").read_text()
    assert "port=8080" in app_text
    assert (tmp_path / "Dockerfile").exists()
