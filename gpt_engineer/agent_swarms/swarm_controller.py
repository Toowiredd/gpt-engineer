"""Controller for running multiple SimpleAgent instances concurrently."""
import tempfile
import threading
from typing import List

from gpt_engineer.core.default.simple_agent import SimpleAgent
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt


def run_task_swarm(prompt: Prompt, steps: List[str]) -> FilesDict:
    """Run micro-steps of a task concurrently using multiple SimpleAgents.

    Each step text is appended to the base ``prompt`` and executed in a
    separate ``SimpleAgent``. The resulting ``FilesDict`` objects are merged and
    returned.
    """

    results: List[FilesDict] = []
    results_lock = threading.Lock()

    def _run(step: str) -> None:
        agent = SimpleAgent.with_default_config(tempfile.mkdtemp())
        step_prompt = Prompt(prompt.text + "\n" + step,
                             prompt.image_urls,
                             entrypoint_prompt=prompt.entrypoint_prompt)
        files = agent.init(step_prompt)
        with results_lock:
            results.append(files)

    threads = [threading.Thread(target=_run, args=(s,)) for s in steps]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    merged: FilesDict = FilesDict()
    for files in results:
        merged.update(files)
    return merged
