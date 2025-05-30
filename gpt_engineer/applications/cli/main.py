"""
Entrypoint for the CLI tool.

This module serves as the entry point for a command-line interface (CLI) tool.
It is designed to interact with OpenAI's language models.
The module provides functionality to:
- Load necessary environment variables,
- Configure various parameters for the AI interaction,
- Manage the generation or improvement of code projects.

Main Functionality
------------------
- Load environment variables required for OpenAI API interaction.
- Parse user-specified parameters for project configuration and AI behavior.
- Facilitate interaction with AI models, databases, and archival processes.

Notes
-----
- The `OPENAI_API_KEY` must be set in the environment or provided in a `.env` file within the working directory.
- The default project path is `projects/example`.
- When using the `azure_endpoint` parameter, provide the Azure OpenAI service endpoint URL.
"""

import difflib
import json
import logging
import os
import platform
import subprocess
import sys

from pathlib import Path

import openai
import typer

from dotenv import load_dotenv
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from termcolor import colored

from gpt_engineer.applications.cli.cli_agent import CliAgent
from gpt_engineer.applications.cli.collect import collect_and_send_human_review
from gpt_engineer.applications.cli.file_selector import FileSelector
from gpt_engineer.applications.gui.advanced_gui import run as run_advanced_gui
from gpt_engineer.applications.gui.main import run as run_gui
from gpt_engineer.core.ai import AI, ClipboardAI
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.file_store import FileStore
from gpt_engineer.core.default.paths import PREPROMPTS_PATH, memory_path
from gpt_engineer.core.default.steps import (
    execute_entrypoint,
    gen_code,
    handle_improve_mode,
    improve_fn as improve_fn,
)
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.git import stage_uncommitted_to_git
from gpt_engineer.core.preprompts_holder import PrepromptsHolder
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.tools.custom_steps import clarified_gen, lite_gen, self_heal

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]}
)  # creates a CLI app


def load_env_if_needed():
    if os.getenv("OPENAI_API_KEY") is None:
        load_dotenv()
    if os.getenv("OPENAI_API_KEY") is None:
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

    openai.api_key = os.getenv("OPENAI_API_KEY")

    if os.getenv("ANTHROPIC_API_KEY") is None:
        load_dotenv()
    if os.getenv("ANTHROPIC_API_KEY") is None:
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


def concatenate_paths(base_path, sub_path):
    relative_path = os.path.relpath(sub_path, base_path)
    if not relative_path.startswith(".."):
        return sub_path
    return os.path.normpath(os.path.join(base_path, sub_path))


def load_prompt(
    input_repo: DiskMemory,
    improve_mode: bool,
    prompt_file: str,
    image_directory: str,
    entrypoint_prompt_file: str = "",
) -> Prompt:
    if os.path.isdir(prompt_file):
        raise ValueError(
            f"The path to the prompt, {prompt_file}, already exists as a directory. No prompt can be read from it. Please specify a prompt file using --prompt_file"
        )
    prompt_str = input_repo.get(prompt_file)
    if prompt_str:
        print(colored("Using prompt from file:", "green"), prompt_file)
        print(prompt_str)
    else:
        if not improve_mode:
            prompt_str = input(
                "\nWhat application do you want gpt-engineer to generate?\n"
            )
        else:
            prompt_str = input("\nHow do you want to improve the application?\n")

    if entrypoint_prompt_file == "":
        entrypoint_prompt = ""
    else:
        full_entrypoint_prompt_file = concatenate_paths(
            input_repo.path, entrypoint_prompt_file
        )
        if os.path.isfile(full_entrypoint_prompt_file):
            entrypoint_prompt = input_repo.get(full_entrypoint_prompt_file)
        else:
            raise ValueError("The provided file at --entrypoint-prompt does not exist")

    if image_directory == "":
        return Prompt(prompt_str, entrypoint_prompt=entrypoint_prompt)

    full_image_directory = concatenate_paths(input_repo.path, image_directory)
    if os.path.isdir(full_image_directory):
        if len(os.listdir(full_image_directory)) == 0:
            raise ValueError("The provided --image_directory is empty.")
        image_repo = DiskMemory(full_image_directory)
        return Prompt(
            prompt_str,
            image_repo.get(".").to_dict(),
            entrypoint_prompt=entrypoint_prompt,
        )
    else:
        raise ValueError("The provided --image_directory is not a directory.")


def get_preprompts_path(use_custom_preprompts: bool, input_path: Path) -> Path:
    original_preprompts_path = PREPROMPTS_PATH
    if not use_custom_preprompts:
        return original_preprompts_path

    custom_preprompts_path = input_path / "preprompts"
    if not custom_preprompts_path.exists():
        custom_preprompts_path.mkdir()

    for file in original_preprompts_path.glob("*"):
        if not (custom_preprompts_path / file.name).exists():
            (custom_preprompts_path / file.name).write_text(file.read_text())
    return custom_preprompts_path


def compare(f1: FilesDict, f2: FilesDict):
    def colored_diff(s1, s2):
        lines1 = s1.splitlines()
        lines2 = s2.splitlines()
        diff = difflib.unified_diff(lines1, lines2, lineterm="")
        RED = "\033[38;5;202m"
        GREEN = "\033[92m"
        RESET = "\033[0m"
        colored_lines = []
        for line in diff:
            if line.startswith("+"):
                colored_lines.append(GREEN + line + RESET)
            elif line.startswith("-"):
                colored_lines.append(RED + line + RESET)
            else:
                colored_lines.append(line)
        return "\n".join(colored_lines)

    for file in sorted(set(f1) | set(f2)):
        diff = colored_diff(f1.get(file, ""), f2.get(file, ""))
        if diff:
            print(f"Changes to {file}:")
            print(diff)


def prompt_yesno() -> bool:
    TERM_CHOICES = colored("y", "green") + "/" + colored("n", "red") + " "
    while True:
        response = input(TERM_CHOICES).strip().lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            break
        print("Please respond with 'y' or 'n'")


def get_system_info():
    system_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "packages": format_installed_packages(get_installed_packages()),
    }
    return system_info


def get_installed_packages():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
        )
        packages = json.loads(result.stdout)
        return {pkg["name"]: pkg["version"] for pkg in packages}
    except Exception as e:
        return str(e)


def format_installed_packages(packages):
    return "\n".join([f"{name}: {version}" for name, version in packages.items()])


@app.command(
    help="""
        GPT-engineer lets you:

        \b
        - Specify a software in natural language
        - Sit back and watch as an AI writes and executes the code
        - Ask the AI to implement improvements
    """
)
def main(
    project_path: str = typer.Argument(".", help="path"),
    model: str = typer.Option(
        os.environ.get("MODEL_NAME", "gpt-4o"), "--model", "-m", help="model id string"
    ),
    temperature: float = typer.Option(
        0.1,
        "--temperature",
        "-t",
        help="Controls randomness: lower values for more focused, deterministic outputs",
    ),
    improve_mode: bool = typer.Option(
        False,
        "--improve",
        "-i",
        help="Improve an existing project by modifying the files.",
    ),
    lite_mode: bool = typer.Option(
        False,
        "--lite",
        "-l",
        help="Lite mode: run a generation using only the main prompt.",
    ),
    clarify_mode: bool = typer.Option(
        False,
        "--clarify",
        "-c",
        help="Clarify mode - discuss specification with AI before implementation.",
    ),
    self_heal_mode: bool = typer.Option(
        False,
        "--self-heal",
        "-sh",
        help="Self-heal mode - fix the code by itself when it fails.",
    ),
    microservice: bool = typer.Option(
        False,
        "--microservice",
        help="Generate a boilerplate microservice instead of using the LLM.",
    ),
    azure_endpoint: str = typer.Option(
        "",
        "--azure",
        "-a",
        help="""Endpoint for your Azure OpenAI Service (https://xx.openai.azure.com).
            In that case, the given model is the deployment name chosen in the Azure AI Studio.""",
    ),
    use_custom_preprompts: bool = typer.Option(
        False,
        "--use-custom-preprompts",
        help="""Use your project's custom preprompts instead of the default ones.
          Copies all original preprompts to the project's workspace if they don't exist there.""",
    ),
    llm_via_clipboard: bool = typer.Option(
        False,
        "--llm-via-clipboard",
        help="Use the clipboard to communicate with the AI.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging for debugging."
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug mode for debugging."
    ),
    gui: bool = typer.Option(
        False,
        "--gui",
        "-g",
        help="Launch the graphical interface instead of running in the console.",
    ),
    advanced_gui: bool = typer.Option(
        False,
        "--advanced-gui",
        help="Launch the advanced web interface instead of running in the console.",
    ),
    advanced_gui_host: str = typer.Option(
        "127.0.0.1",
        "--advanced-gui-host",
        help="Host for the advanced GUI.",
    ),
    advanced_gui_port: int = typer.Option(
        5000,
        "--advanced-gui-port",
        help="Port for the advanced GUI.",
    ),
    prompt_file: str = typer.Option(
        "prompt",
        "--prompt_file",
        help="Relative path to a text file containing a prompt.",
    ),
    entrypoint_prompt_file: str = typer.Option(
        "",
        "--entrypoint_prompt",
        help="Relative path to a text file containing a file that specifies requirements for you entrypoint.",
    ),
    image_directory: str = typer.Option(
        "",
        "--image_directory",
        help="Relative path to a folder containing images.",
    ),
    use_cache: bool = typer.Option(
        False,
        "--use_cache",
        help="Speeds up computations and saves tokens when running the same prompt multiple times by caching the LLM response.",
    ),
    skip_file_selection: bool = typer.Option(
        False,
        "--skip-file-selection",
        "-s",
        help="Skip interactive file selection in improve mode and use the generated TOML file directly.",
    ),
    no_execution: bool = typer.Option(
        False,
        "--no_execution",
        help="Run setup but to not call LLM or write any code. For testing purposes.",
    ),
    sysinfo: bool = typer.Option(
        False,
        "--sysinfo",
        help="Output system information for debugging",
    ),
    diff_timeout: int = typer.Option(
        3,
        "--diff_timeout",
        help="Diff regexp timeout. Default: 3. Increase if regexp search timeouts.",
    ),
):
    if debug:
        import pdb

        sys.excepthook = lambda *_: pdb.pm()

    if sysinfo:
        sys_info = get_system_info()
        for key, value in sys_info.items():
            print(f"{key}: {value}")
        raise typer.Exit()

    if gui:
        run_gui(project_path)
        raise typer.Exit()

    if advanced_gui:
        run_advanced_gui(project_path, host=advanced_gui_host, port=advanced_gui_port)
        raise typer.Exit()

    if improve_mode and (clarify_mode or lite_mode):
        typer.echo("Error: Clarify and lite mode are not compatible with improve mode.")
        raise typer.Exit(code=1)

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if use_cache:
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))
    if improve_mode:
        assert not (
            clarify_mode or lite_mode
        ), "Clarify and lite mode are not active for improve mode"

    load_env_if_needed()

    if llm_via_clipboard:
        ai = ClipboardAI()
    else:
        ai = AI(
            model_name=model,
            temperature=temperature,
            azure_endpoint=azure_endpoint,
        )

    path = Path(project_path)
    print("Running gpt-engineer in", path.absolute(), "\n")

    prompt = load_prompt(
        DiskMemory(path),
        improve_mode,
        prompt_file,
        image_directory,
        entrypoint_prompt_file,
    )

    if microservice:
        from gpt_engineer.applications.service_generator.api_automator import (
            generate_microservice,
        )

        generate_microservice(path, prompt.text)
        print(f"Microservice files created in {path}")
        return

    if not ai.vision:
        prompt.image_urls = None

    if clarify_mode:
        code_gen_fn = clarified_gen
    elif lite_mode:
        code_gen_fn = lite_gen
    else:
        code_gen_fn = gen_code

    if self_heal_mode:
        execution_fn = self_heal
    else:
        execution_fn = execute_entrypoint

    preprompts_holder = PrepromptsHolder(
        get_preprompts_path(use_custom_preprompts, Path(project_path))
    )

    memory = DiskMemory(memory_path(project_path))
    memory.archive_logs()

    execution_env = DiskExecutionEnv()
    agent = CliAgent.with_default_config(
        memory,
        execution_env,
        ai=ai,
        code_gen_fn=code_gen_fn,
        improve_fn=improve_fn,
        process_code_fn=execution_fn,
        preprompts_holder=preprompts_holder,
    )

    files = FileStore(project_path)
    if not no_execution:
        if improve_mode:
            files_dict_before, is_linting = FileSelector(project_path).ask_for_files(
                skip_file_selection=skip_file_selection
            )
            if is_linting:
                files_dict_before = files.linting(files_dict_before)
            files_dict = handle_improve_mode(
                prompt, agent, memory, files_dict_before, diff_timeout=diff_timeout
            )
            if not files_dict or files_dict_before == files_dict:
                print(
                    f"No changes applied. Could you please upload the debug_log_file.txt in {memory.path}/logs folder in a github issue?"
                )
            else:
                print("\nChanges to be made:")
                compare(files_dict_before, files_dict)
                print()
                print(colored("Do you want to apply these changes?", "light_green"))
                if not prompt_yesno():
                    files_dict = files_dict_before
        else:
            files_dict = agent.init(prompt)
            config = (code_gen_fn.__name__, execution_fn.__name__)
            collect_and_send_human_review(prompt, model, temperature, config, memory)

        stage_uncommitted_to_git(path, files_dict, improve_mode)
        files.push(files_dict)

    if ai.token_usage_log.is_openai_model():
        print("Total api cost: $ ", ai.token_usage_log.usage_cost())
    elif os.getenv("LOCAL_MODEL"):
        print("Total api cost: $ 0.0 since we are using local LLM.")
    else:
        print("Total tokens used: ", ai.token_usage_log.total_tokens())


if __name__ == "__main__":
    app()
