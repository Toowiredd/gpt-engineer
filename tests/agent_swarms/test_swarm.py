import time

from gpt_engineer.agent_swarms import swarm_controller
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt


class DummyAgent:
    @classmethod
    def with_default_config(cls, *_args, **_kwargs):
        return cls()

    def init(self, prompt: Prompt) -> FilesDict:
        time.sleep(0.2)
        key = prompt.text.strip()
        return FilesDict({key: "done"})


def test_run_task_swarm_parallel(monkeypatch):
    monkeypatch.setattr(swarm_controller, "SimpleAgent", DummyAgent)
    start = time.perf_counter()
    result = swarm_controller.run_task_swarm(Prompt("task"), ["step1", "step2"])
    duration = time.perf_counter() - start
    assert duration < 0.35
    assert result == {"task\nstep1": "done", "task\nstep2": "done"}

