"""Template loader for system prompts and other content."""

from pathlib import Path
from typing import Any, Optional


class TemplateLoader:
    """Loads and manages templates for chaobot."""

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """Initialize template loader.

        Args:
            template_dir: Directory containing templates (default: chaobot/templates)
        """
        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = Path(__file__).parent

    def load(self, name: str) -> str:
        """Load a template by name.

        Args:
            name: Template name (without .md extension)

        Returns:
            Template content

        Raises:
            FileNotFoundError: If template not found
        """
        template_path = self.template_dir / f"{name}.md"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {name}")

        return template_path.read_text(encoding="utf-8")

    def load_system_prompt(self) -> str:
        """Load the default system prompt.

        Returns:
            System prompt content
        """
        try:
            return self.load("system_prompt")
        except FileNotFoundError:
            return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Return default system prompt if template not found."""
        return """You are chaobot, a helpful AI assistant.

You have access to tools that can help you accomplish tasks. Use them when appropriate.

Guidelines:
- Be concise but thorough
- Ask clarifying questions if needed
- Use tools to gather information or perform actions
- Always prioritize user safety and privacy
"""

    def render(self, name: str, **kwargs: Any) -> str:
        """Render a template with variables.

        Args:
            name: Template name
            **kwargs: Variables to substitute

        Returns:
            Rendered template content
        """
        content = self.load(name)

        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))

        return content

    def exists(self, name: str) -> bool:
        """Check if a template exists.

        Args:
            name: Template name

        Returns:
            True if template exists
        """
        template_path = self.template_dir / f"{name}.md"
        return template_path.exists()


_template_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """Get the global template loader instance.

    Returns:
        TemplateLoader instance
    """
    global _template_loader

    if _template_loader is None:
        _template_loader = TemplateLoader()

    return _template_loader
