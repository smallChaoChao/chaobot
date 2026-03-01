"""Skill loader for chaobot.

Loads and manages agent skills from SKILL.md files.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()

# Built-in skills directory
BUILTIN_SKILLS_DIR = Path(__file__).parent

# Default workspace directory
DEFAULT_WORKSPACE = Path.home() / ".chaobot" / "workspace"


class SkillsLoader:
    """Loader for agent skills.

    Skills are markdown files (SKILL.md) that teach the agent how to use
    specific tools or perform certain tasks.

    Example:
        loader = SkillsLoader()
        skills = loader.list_skills()
        content = loader.load_skill("weather")
    """

    def __init__(self, workspace: Path | None = None) -> None:
        """Initialize skills loader.

        Args:
            workspace: Workspace directory for user skills
        """
        if workspace is None:
            workspace = DEFAULT_WORKSPACE

        self.workspace = workspace
        self.workspace_skills = workspace / "skills"
        self.builtin_skills = BUILTIN_SKILLS_DIR

        # Ensure directories exist
        self.workspace_skills.mkdir(parents=True, exist_ok=True)

    def list_skills(self, check_requirements: bool = True) -> list[dict[str, Any]]:
        """List all available skills.

        Args:
            check_requirements: Whether to check if requirements are met

        Returns:
            List of skill info dictionaries
        """
        skills = []
        seen = set()

        # Workspace skills take priority
        for skill_dir in [self.workspace_skills, self.builtin_skills]:
            if not skill_dir.exists():
                continue

            for skill_path in skill_dir.iterdir():
                if not skill_path.is_dir():
                    continue

                skill_file = skill_path / "SKILL.md"
                if not skill_file.exists():
                    continue

                name = skill_path.name
                if name in seen:
                    continue
                seen.add(name)

                # Parse metadata
                meta = self._parse_metadata(skill_file)

                skill_info = {
                    "name": name,
                    "description": meta.get("description", ""),
                    "location": str(skill_file),
                    "always": meta.get("always", False),
                    "metadata": meta,
                }

                if check_requirements:
                    skill_info["available"] = self._check_requirements(meta)
                    if not skill_info["available"]:
                        skill_info["requires"] = self._get_missing_requirements(meta)

                skills.append(skill_info)

        return sorted(skills, key=lambda x: x["name"])

    def load_skill(self, name: str) -> str | None:
        """Load a skill's content.

        Args:
            name: Skill name

        Returns:
            Skill content or None if not found
        """
        skill_file = self._find_skill_file(name)
        if not skill_file:
            return None

        return skill_file.read_text(encoding="utf-8")

    def load_skill_body(self, name: str) -> str | None:
        """Load a skill's body (without frontmatter).

        Args:
            name: Skill name

        Returns:
            Skill body content or None if not found
        """
        content = self.load_skill(name)
        if not content:
            return None

        # Remove YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()

        return content

    def load_skills_for_context(self, names: list[str]) -> str:
        """Load multiple skills for context building.

        Args:
            names: List of skill names

        Returns:
            Combined skill content
        """
        parts = []
        for name in names:
            content = self.load_skill_body(name)
            if content:
                parts.append(f"## {name}\n\n{content}")

        return "\n\n".join(parts)

    def get_always_skills(self) -> list[str]:
        """Get skills marked as always=true.

        Returns:
            List of skill names
        """
        always = []
        for skill in self.list_skills(check_requirements=True):
            if skill.get("always") and skill.get("available"):
                always.append(skill["name"])
        return always

    def build_skills_summary(self) -> str:
        """Build XML-formatted skills summary for context.

        Returns:
            XML string of available skills
        """
        skills = self.list_skills(check_requirements=True)
        if not skills:
            return ""

        lines = ["<skills>"]
        for skill in skills:
            available = "true" if skill.get("available") else "false"
            lines.append(f'  <skill available="{available}">')
            lines.append(f"    <name>{skill['name']}</name>")
            lines.append(f"    <description>{skill['description']}</description>")
            lines.append(f"    <location>{skill['location']}</location>")
            if "requires" in skill:
                lines.append(f"    <requires>{skill['requires']}</requires>")
            lines.append("  </skill>")
        lines.append("</skills>")

        return "\n".join(lines)

    def install_skill(self, name: str, content: str) -> bool:
        """Install a skill to workspace.

        Args:
            name: Skill name
            content: SKILL.md content

        Returns:
            True if installed successfully
        """
        try:
            skill_dir = self.workspace_skills / name
            skill_dir.mkdir(parents=True, exist_ok=True)

            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(content, encoding="utf-8")

            console.print(f"[green]✅ Skill '{name}' installed[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to install skill '{name}': {e}[/red]")
            return False

    def _find_skill_file(self, name: str) -> Path | None:
        """Find skill file by name.

        Args:
            name: Skill name

        Returns:
            Path to SKILL.md or None
        """
        # Check workspace first
        for skill_dir in [self.workspace_skills, self.builtin_skills]:
            skill_file = skill_dir / name / "SKILL.md"
            if skill_file.exists():
                return skill_file
        return None

    def _parse_metadata(self, skill_file: Path) -> dict[str, Any]:
        """Parse YAML frontmatter from skill file.

        Args:
            skill_file: Path to SKILL.md

        Returns:
            Metadata dictionary
        """
        content = skill_file.read_text(encoding="utf-8")

        if not content.startswith("---"):
            return {}

        # Extract YAML frontmatter
        match = re.match(r"---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}

        yaml_content = match.group(1)
        metadata = {}

        # Simple YAML parsing (key: value)
        for line in yaml_content.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                # Handle special fields
                if key == "always":
                    value = value.lower() == "true"
                elif key == "metadata":
                    # JSON metadata
                    try:
                        import json
                        value = json.loads(value)
                    except:
                        value = {}

                metadata[key] = value

        return metadata

    def _check_requirements(self, meta: dict[str, Any]) -> bool:
        """Check if skill requirements are met.

        Args:
            meta: Skill metadata

        Returns:
            True if all requirements are met
        """
        nanobot_meta = meta.get("metadata", {}).get("chaobot", {})
        requires = nanobot_meta.get("requires", {})

        # Check required binaries
        for binary in requires.get("bins", []):
            if not shutil.which(binary):
                return False

        # Check required environment variables
        for env in requires.get("env", []):
            if not os.environ.get(env):
                return False

        return True

    def _get_missing_requirements(self, meta: dict[str, Any]) -> str:
        """Get missing requirements description.

        Args:
            meta: Skill metadata

        Returns:
            Description of missing requirements
        """
        nanobot_meta = meta.get("metadata", {}).get("chaobot", {})
        requires = nanobot_meta.get("requires", {})

        missing = []

        for binary in requires.get("bins", []):
            if not shutil.which(binary):
                missing.append(f"CLI: {binary}")

        for env in requires.get("env", []):
            if not os.environ.get(env):
                missing.append(f"ENV: {env}")

        return ", ".join(missing) if missing else ""


# Global skills loader instance
_skills_loader: SkillsLoader | None = None


def get_skills_loader(workspace: Path | None = None) -> SkillsLoader:
    """Get global skills loader instance.

    Args:
        workspace: Optional workspace directory

    Returns:
        SkillsLoader instance
    """
    global _skills_loader
    if _skills_loader is None:
        _skills_loader = SkillsLoader(workspace)
    return _skills_loader
