"""Skills system for chaobot.

Skills are markdown files (SKILL.md) that teach the agent how to use
specific tools or perform certain tasks.

Based on nanobot's skill system design.
"""

from chaobot.skills.loader import SkillsLoader, get_skills_loader

__all__ = ["SkillsLoader", "get_skills_loader"]
