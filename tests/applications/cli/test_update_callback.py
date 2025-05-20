import tempfile

from gpt_engineer.applications.cli.cli_agent import CliAgent
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.paths import PREPROMPTS_PATH, memory_path
from gpt_engineer.core.ai import AI
from gpt_engineer.tools.custom_steps import lite_gen
from tests.mock_ai import MockAI


def test_set_update_callback_forwards_messages(tmp_path):
    memory = DiskMemory(memory_path(tmp_path))
    execution_env = DiskExecutionEnv()
    mock_ai = MockAI([])
    agent = CliAgent.with_default_config(memory, execution_env, ai=mock_ai)
    received = []
    agent.set_update_callback(lambda m: received.append(m))
    agent._send_update("status")
    assert received == ["status"]

