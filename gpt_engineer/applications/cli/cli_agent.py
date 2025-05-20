"""
This module provides the CliAgent class which manages the lifecycle of code generation and improvement
using an AI model. It includes functionalities to initialize code generation, improve existing code,
and process the code through various steps defined in the step bundle.
"""

from typing import Callable, Optional, TypeVar

# from gpt_engineer.core.default.git_version_manager import GitVersionManager
from gpt_engineer.core.ai import AI
from gpt_engineer.core.base_agent import BaseAgent
from gpt_engineer.core.base_execution_env import BaseExecutionEnv
from gpt_engineer.core.base_memory import BaseMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.paths import PREPROMPTS_PATH
from gpt_engineer.core.default.steps import (
    execute_entrypoint,
    gen_code,
    gen_entrypoint,
    improve_fn,
)
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.preprompts_holder import PrepromptsHolder
from gpt_engineer.core.prompt import Prompt

CodeGenType = TypeVar("CodeGenType", bound=Callable[[AI, str, BaseMemory], FilesDict])
CodeProcessor = TypeVar(
    "CodeProcessor", bound=Callable[[AI, BaseExecutionEnv, FilesDict], FilesDict]
)
ImproveType = TypeVar(
    "ImproveType", bound=Callable[[AI, str, FilesDict, BaseMemory], FilesDict]
)

class CliAgent(BaseAgent):
    """
    The `CliAgent` class is responsible for managing the lifecycle of code generation and improvement
    using an AI model. It orchestrates the generation of new code and the improvement of existing code
    based on given prompts and utilizes a memory system and execution environment for processing.

    Parameters
    ----------
    memory : BaseMemory
        An instance of a class that adheres to the BaseMemory interface, used for storing and retrieving
        information during the code generation process.
    execution_env : BaseExecutionEnv
        An instance of a class that adheres to the BaseExecutionEnv interface, used for executing code
        and managing the execution environment.
    ai : AI, optional
        An instance of the AI class that manages calls to the language model. If not provided, a default
        instance is created.
    code_gen_fn : CodeGenType, optional
        A callable that takes an AI instance, a prompt, and a memory instance to generate code. Defaults
        to the `gen_code` function.
    improve_fn : ImproveType, optional
        A callable that takes an AI instance, a prompt, a FilesDict instance, and a memory instance to
        improve code. Defaults to the `improve` function.
    process_code_fn : CodeProcessor, optional
        A callable that takes an AI instance, an execution environment, and a FilesDict instance to
        process code. Defaults to the `execute_entrypoint` function.
    preprompts_holder : PrepromptsHolder, optional
        An instance of PrepromptsHolder that manages preprompt templates. If not provided, a default
        instance is created using the PREPROMPTS_PATH.

    Attributes
    ----------
    memory : BaseMemory
        The memory instance where the agent stores and retrieves information.
    execution_env : BaseExecutionEnv
        The execution environment instance where the agent executes and manages code.
    ai : AI
        The AI instance used for interacting with the language model.
    code_gen_fn : CodeGenType
        The function used for generating code.
    improve_fn : ImproveType
        The function used for improving code.
    process_code_fn : CodeProcessor
        The function used for processing code.
    preprompts_holder : PrepromptsHolder
        The holder for preprompt templates.
    """

    def __init__(
        self,
        memory: BaseMemory,
        execution_env: BaseExecutionEnv,
        ai: AI = None,
        code_gen_fn: CodeGenType = gen_code,
        improve_fn: ImproveType = improve_fn,
        process_code_fn: CodeProcessor = execute_entrypoint,
        preprompts_holder: PrepromptsHolder = None,
    ):
        self.memory = memory
        self.execution_env = execution_env
        self.ai = ai or AI()
        self.code_gen_fn = code_gen_fn
        self.process_code_fn = process_code_fn
        self.improve_fn = improve_fn
        self.preprompts_holder = preprompts_holder or PrepromptsHolder(PREPROMPTS_PATH)
        self._update_callback: Optional[Callable[[str], None]] = None

    def set_update_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for status updates."""
        self._update_callback = callback

    def _send_update(self, message: str) -> None:
        if self._update_callback:
            self._update_callback(message)

    @classmethod
    def with_default_config(
        cls,
        memory: DiskMemory,
        execution_env: DiskExecutionEnv,
        ai: AI = None,
        code_gen_fn: CodeGenType = gen_code,
        improve_fn: ImproveType = improve_fn,
        process_code_fn: CodeProcessor = execute_entrypoint,
        preprompts_holder: PrepromptsHolder = None,
        diff_timeout=3,
    ):
        """
        Creates a new instance of CliAgent with default configurations for memory, execution environment,
        AI, and other functional parameters.
        """
        if not isinstance(memory, DiskMemory):
            raise TypeError("memory must be an instance of DiskMemory")
        if not isinstance(execution_env, DiskExecutionEnv):
            raise TypeError("execution_env must be an instance of DiskExecutionEnv")

        return cls(
            memory=memory,
            execution_env=execution_env,
            ai=ai,
            code_gen_fn=code_gen_fn,
            process_code_fn=process_code_fn,
            improve_fn=improve_fn,
            preprompts_holder=preprompts_holder or PrepromptsHolder(PREPROMPTS_PATH),
        )

    def init(self, prompt: Prompt) -> FilesDict:
        """
        Generates a new piece of code using the AI and step bundle based on the provided prompt.
        """
        self._send_update("init_start")
        files_dict = self.code_gen_fn(
            self.ai, prompt, self.memory, self.preprompts_holder
        )
        entrypoint = gen_entrypoint(
            self.ai, prompt, files_dict, self.memory, self.preprompts_holder
        )
        combined_dict = {**files_dict, **entrypoint}
        files_dict = FilesDict(combined_dict)
        files_dict = self.process_code_fn(
            self.ai,
            self.execution_env,
            files_dict,
            preprompts_holder=self.preprompts_holder,
            prompt=prompt,
            memory=self.memory,
        )
        self._send_update("init_end")
        return files_dict

    def improve(
        self,
        files_dict: FilesDict,
        prompt: Prompt,
        execution_command: Optional[str] = None,
        diff_timeout=3,
    ) -> FilesDict:
        """
        Improves an existing piece of code using the AI and step bundle based on the provided prompt.
        """
        self._send_update("improve_start")
        files_dict = self.improve_fn(
            self.ai,
            prompt,
            files_dict,
            self.memory,
            self.preprompts_holder,
            diff_timeout=diff_timeout,
        )
        self._send_update("improve_end")
        return files_dict