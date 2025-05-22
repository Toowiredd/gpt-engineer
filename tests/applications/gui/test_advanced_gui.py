import pytest

try:
    from flask import Flask

    from gpt_engineer.applications.gui.advanced_gui import create_app
except Exception:
    Flask = None
    create_app = None


def test_create_app(tmp_path):
    if Flask is None or create_app is None:  # pragma: no cover - dependency missing
        pytest.skip("Flask not available")
    p = tmp_path / "projects/example"
    p.mkdir(parents=True)
    (p / "prompt").write_text("hi")
    app = create_app(p)
    assert isinstance(app, Flask)
    routes = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "status" in routes
