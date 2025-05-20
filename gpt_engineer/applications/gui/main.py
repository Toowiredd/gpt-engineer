
"""A basic Tkinter GUI for interacting with the CLI agent."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from pathlib import Path

from gpt_engineer.applications.cli.cli_agent import CliAgent
from gpt_engineer.applications.gui.templates import TemplateManager
from gpt_engineer.applications.service_generator.api_automator import generate_microservice
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.file_store import FileStore
from gpt_engineer.core.default.paths import memory_path
from gpt_engineer.core.prompt import Prompt


class Application(tk.Tk):
    def __init__(self, project_path: Path) -> None:
        super().__init__()
        self.title("gpt-engineer GUI")
        self.geometry("600x400")

        self.project_path = Path(project_path)
        self.memory = DiskMemory(memory_path(self.project_path))
        self.execution_env = DiskExecutionEnv()
        self.agent = CliAgent.with_default_config(self.memory, self.execution_env)
        self.agent.set_update_callback(self.append_status)
        self.file_store = FileStore(self.project_path)

        self.template_manager = TemplateManager()
        self.templates = self.template_manager.list_templates()

        self.prompt_entry = tk.Text(self, height=10)
        self.prompt_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if self.templates:
            self.template_var = tk.StringVar(value=list(self.templates.keys())[0])
            tk.OptionMenu(
                self,
                self.template_var,
                *self.templates.keys(),
                command=self.on_template_selected,
            ).pack(pady=5)

        self.generate_button = tk.Button(
            self, text="Generate", command=self.on_generate_click
        )
        self.generate_button.pack(pady=5)

        tk.Button(
            self,
            text="Generate Microservice",
            command=self.on_microservice_click,
        ).pack(pady=5)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var).pack(pady=5)
        self.log = tk.Text(self, height=6, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def on_generate_click(self) -> None:
        prompt_text = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt_text:
            self.status_var.set("Please enter a prompt")
            return
        prompt = Prompt(prompt_text)
        self.generate_button.config(state=tk.DISABLED)
        files_dict = self.agent.init(prompt)
        self.file_store.push(files_dict)
        self.status_var.set("Generation complete")
        self.generate_button.config(state=tk.NORMAL)

    def on_template_selected(self, name: str) -> None:
        template = self.templates.get(name)
        if template:
            self.prompt_entry.delete("1.0", tk.END)
            self.prompt_entry.insert(tk.END, template.content)

    def on_microservice_click(self) -> None:
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Prompt cannot be empty")
            return
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            generate_microservice(Path(directory), prompt)
            messagebox.showinfo("Done", f"Microservice generated in {directory}")

    def append_status(self, message: str) -> None:
        self.status_var.set(message)
        self.log.configure(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.configure(state="disabled")


def run(project_path: str = "projects/example") -> None:
    app = Application(Path(project_path))
    app.mainloop()
