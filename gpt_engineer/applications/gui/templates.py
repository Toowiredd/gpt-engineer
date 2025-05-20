"""Utilities for loading and applying predefined GUI templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class Template:
    """Representation of a GUI template."""

    name: str
    description: str
    content: str


class TemplateManager:
    """Manage GUI templates stored as files."""

    def __init__(self, templates_dir: Path | str | None = None) -> None:
        self.templates_dir = Path(templates_dir or Path(__file__).parent / "templates")
        self.templates_dir.mkdir(exist_ok=True)

    def list_templates(self) -> Dict[str, Template]:
        """Return a mapping of template name to :class:`Template`."""
        templates: Dict[str, Template] = {}
        for file in self.templates_dir.glob("*.txt"):
            templates[file.stem] = Template(
                name=file.stem,
                description=file.stem.replace("_", " "),
                content=file.read_text(),
            )
        return templates

    def load(self, name: str) -> Template | None:
        """Load a template by name."""
        path = self.templates_dir / f"{name}.txt"
        if not path.exists():
            return None
        return Template(
            name=name, description=name.replace("_", " "), content=path.read_text()
        )

    def apply(self, name: str) -> str:
        """Return the content of a template or an empty string."""
        template = self.load(name)
        return template.content if template else ""
