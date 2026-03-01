"""Smart skill selector for chaobot.

This module implements intelligent skill selection based on user intent,
referencing nanobot and OpenClaw's skill triggering mechanisms.
"""

import re
from dataclasses import dataclass
from typing import Any

from chaobot.skills.loader import SkillsLoader


@dataclass
class SkillMatch:
    """Skill match result."""

    name: str
    description: str
    confidence: float  # 0.0 to 1.0
    reason: str
    triggers: list[str]


class SkillSelector:
    """Intelligent skill selector.

    Analyzes user input and selects the most appropriate skills.
    Inspired by nanobot's description-based triggering and OpenClaw's
    intent recognition.
    """

    def __init__(self, loader: SkillsLoader) -> None:
        """Initialize skill selector.

        Args:
            loader: Skills loader instance
        """
        self.loader = loader

    def select_skills(
        self,
        user_input: str,
        max_skills: int = 3,
        min_confidence: float = 0.3
    ) -> list[SkillMatch]:
        """Select relevant skills for user input.

        Args:
            user_input: User's message
            max_skills: Maximum number of skills to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of skill matches sorted by confidence
        """
        matches = []
        user_lower = user_input.lower()

        # Get all available skills
        skills = self.loader.list_skills(check_requirements=True)

        for skill in skills:
            if not skill.get("available", True):
                continue

            name = skill["name"]
            description = skill.get("description", "").lower()

            # Calculate match confidence
            confidence, reason, triggers = self._calculate_confidence(
                user_lower, name.lower(), description
            )

            if confidence >= min_confidence:
                matches.append(SkillMatch(
                    name=name,
                    description=skill.get("description", ""),
                    confidence=confidence,
                    reason=reason,
                    triggers=triggers
                ))

        # Sort by confidence (descending)
        matches.sort(key=lambda x: x.confidence, reverse=True)

        return matches[:max_skills]

    def _calculate_confidence(
        self,
        user_input: str,
        skill_name: str,
        skill_description: str
    ) -> tuple[float, str, list[str]]:
        """Calculate match confidence between user input and skill.

        Args:
            user_input: User's message (lowercase)
            skill_name: Skill name (lowercase)
            skill_description: Skill description (lowercase)

        Returns:
            Tuple of (confidence, reason, matched_triggers)
        """
        triggers = []
        score = 0.0
        reasons = []

        # 1. Direct skill name mention (highest confidence)
        if skill_name in user_input:
            score += 0.9
            triggers.append(f"skill_name:{skill_name}")
            reasons.append(f"User mentioned skill name '{skill_name}'")

        # 2. Keyword matching from description
        # Extract key terms from description (nouns, verbs, domain terms)
        desc_keywords = self._extract_keywords(skill_description)
        user_keywords = self._extract_keywords(user_input)

        matched_keywords = desc_keywords & user_keywords
        if matched_keywords:
            keyword_score = min(len(matched_keywords) * 0.15, 0.6)
            score += keyword_score
            triggers.extend([f"keyword:{k}" for k in matched_keywords])
            reasons.append(f"Matched keywords: {', '.join(matched_keywords)}")

        # 3. Intent pattern matching
        intent_patterns = self._get_intent_patterns(skill_name)
        for pattern, pattern_score in intent_patterns:
            if pattern in user_input:
                score += pattern_score
                triggers.append(f"intent:{pattern}")
                reasons.append(f"Matched intent pattern '{pattern}'")

        # 4. Domain-specific matching
        domain_score = self._domain_match(user_input, skill_name, skill_description)
        if domain_score > 0:
            score += domain_score
            triggers.append("domain_match")
            reasons.append("Domain context match")

        # Cap at 1.0
        score = min(score, 1.0)

        # Generate summary reason
        if reasons:
            reason = reasons[0]  # Use top reason
        else:
            reason = "No strong match found"

        return score, reason, triggers

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract important keywords from text.

        Args:
            text: Input text

        Returns:
            Set of keywords
        """
        # Common stop words to ignore
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "and", "but", "or", "yet", "so", "if",
            "because", "although", "though", "while", "where", "when",
            "that", "which", "who", "whom", "whose", "what", "this",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "me", "him", "her", "us", "them", "my", "your", "his", "its",
            "our", "their", "mine", "yours", "hers", "ours", "theirs",
            "how", "why", "please", "help", "me", "can", "you"
        }

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter stop words and return unique set
        return set(w for w in words if w not in stop_words)

    def _get_intent_patterns(self, skill_name: str) -> list[tuple[str, float]]:
        """Get intent patterns for a skill.

        Args:
            skill_name: Skill name

        Returns:
            List of (pattern, score) tuples
        """
        # Skill-specific intent patterns
        patterns = {
            "skill-creator": [
                ("create skill", 0.7),
                ("make skill", 0.7),
                ("new skill", 0.7),
                ("build skill", 0.7),
                ("skill development", 0.6),
                ("skill design", 0.6),
                ("how to create", 0.5),
                ("skill template", 0.5),
            ],
            "find-skills": [
                ("find skill", 0.8),
                ("search skill", 0.8),
                ("look for skill", 0.7),
                ("is there a skill", 0.7),
                ("any skill for", 0.7),
                ("how do i", 0.5),
                ("can you help", 0.4),
                ("skill for", 0.6),
            ],
            "self-improvement": [
                ("learn from", 0.6),
                ("remember this", 0.7),
                ("save this", 0.6),
                ("log error", 0.7),
                ("track learning", 0.6),
                ("improve yourself", 0.6),
                ("self improvement", 0.8),
                ("continuous improvement", 0.7),
            ],
            "weather": [
                ("weather", 0.8),
                ("temperature", 0.7),
                ("forecast", 0.7),
                ("rain", 0.6),
                ("sunny", 0.6),
                ("hot", 0.5),
                ("cold", 0.5),
            ],
            "github": [
                ("github", 0.8),
                ("repository", 0.7),
                ("repo", 0.7),
                ("pull request", 0.7),
                ("pr ", 0.6),
                ("commit", 0.6),
                ("branch", 0.6),
                ("merge", 0.6),
            ],
            "memory": [
                ("remember", 0.7),
                ("memorize", 0.7),
                ("save to memory", 0.8),
                ("recall", 0.6),
                ("what did i say", 0.5),
                ("previously", 0.5),
            ],
            "summarize": [
                ("summarize", 0.9),
                ("summary", 0.9),
                ("tl;dr", 0.8),
                ("brief", 0.6),
                ("condense", 0.7),
                ("short version", 0.7),
            ],
            "ui-ux": [
                ("design", 0.6),
                ("ui ", 0.7),
                ("ux", 0.7),
                ("interface", 0.6),
                ("stylesheet", 0.6),
                ("css", 0.5),
                ("layout", 0.5),
                ("color scheme", 0.6),
            ],
        }

        return patterns.get(skill_name, [])

    def _domain_match(
        self,
        user_input: str,
        skill_name: str,
        skill_description: str
    ) -> float:
        """Check domain-specific matching.

        Args:
            user_input: User input
            skill_name: Skill name
            skill_description: Skill description

        Returns:
            Domain match score
        """
        # Domain keywords mapping
        domains = {
            "coding": ["code", "programming", "development", "debug", "function", "class", "api"],
            "writing": ["write", "draft", "compose", "text", "content", "article", "blog"],
            "data": ["data", "csv", "json", "analysis", "statistics", "chart", "graph"],
            "web": ["web", "html", "css", "javascript", "frontend", "backend", "server"],
            "devops": ["deploy", "docker", "kubernetes", "ci/cd", "pipeline", "infrastructure"],
            "design": ["design", "ui", "ux", "interface", "visual", "layout", "style"],
        }

        score = 0.0

        for domain, keywords in domains.items():
            user_has_domain = any(kw in user_input for kw in keywords)
            skill_has_domain = any(kw in skill_description for kw in keywords)

            if user_has_domain and skill_has_domain:
                score += 0.2

        return min(score, 0.4)  # Cap domain bonus

    def build_skill_recommendation(
        self,
        user_input: str,
        max_skills: int = 2
    ) -> str:
        """Build skill recommendation text for context.

        Args:
            user_input: User's message
            max_skills: Maximum skills to recommend

        Returns:
            Recommendation text
        """
        matches = self.select_skills(user_input, max_skills=max_skills)

        if not matches:
            return ""

        lines = ["\n## 🎯 Recommended Skills\n"]

        for i, match in enumerate(matches, 1):
            confidence_pct = int(match.confidence * 100)
            lines.append(
                f"{i}. **[{match.name}]** ({confidence_pct}% match)\n"
                f"   - {match.description}\n"
                f"   - Why: {match.reason}\n"
            )

        lines.append(
            "\nTo use a skill, read its SKILL.md file with the file_read tool.\n"
        )

        return "\n".join(lines)


# Global selector instance
_skill_selector: SkillSelector | None = None


def get_skill_selector(loader: SkillsLoader | None = None) -> SkillSelector:
    """Get global skill selector instance.

    Args:
        loader: Optional skills loader

    Returns:
        SkillSelector instance
    """
    global _skill_selector
    if _skill_selector is None:
        if loader is None:
            from chaobot.skills import get_skills_loader
            loader = get_skills_loader()
        _skill_selector = SkillSelector(loader)
    return _skill_selector
