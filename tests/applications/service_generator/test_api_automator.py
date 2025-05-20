from pathlib import Path

from gpt_engineer.applications.service_generator.api_automator import generate_microservice


def test_generate_microservice(tmp_path: Path):
    prompt = "return 'pong' at /ping"
    generate_microservice(tmp_path, prompt)
    assert (tmp_path / "app.py").exists()
    assert (tmp_path / "Dockerfile").exists()
