import pytest
import typer

from tests.applications.cli.test_main import DefaultArgumentsMain


def test_cli_exits_with_gui(tmp_path):
    p = tmp_path / "projects/example"
    p.mkdir(parents=True)
    (p / "prompt").write_text("hi")
    args = DefaultArgumentsMain(str(p), gui=True, llm_via_clipboard=True, no_execution=True)
    with pytest.raises(typer.Exit):
        args()

