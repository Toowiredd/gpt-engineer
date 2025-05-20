"""Step-by-step wizards helping users set up projects and configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass
class WizardStep:
    prompt: str
    action: Callable[[str], None]


class SetupWizard:
    """Simple console-based wizard for configuring new projects."""

    def __init__(self, steps: List[WizardStep] | None = None) -> None:
        self.steps = steps or []

    def add_step(self, prompt: str, action: Callable[[str], None]) -> None:
        self.steps.append(WizardStep(prompt, action))

    def run(self) -> None:
        for step in self.steps:
            value = input(step.prompt + ": ")
            step.action(value)
