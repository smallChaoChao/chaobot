"""Feishu message formatter for rich text rendering.

Converts markdown-like content to Feishu post format with support for:
- Bold, italic, underline, strikethrough text
- Code blocks with syntax highlighting
- Hyperlinks
- Horizontal rules
- Lists (ordered and unordered)
- Images
- @ mentions
"""

import re
from typing import Any


class FeishuFormatter:
    """Format messages for Feishu rich text display."""

    # Emoji type mapping for common reactions
    EMOJI_TYPES = {
        "ok": "OK",
        "thumbsup": "THUMBSUP",
        "thanks": "THANKS",
        "muscle": "MUSCLE",
        "heart": "HEART",
        "smile": "SMILE",
        "laugh": "LAUGH",
        "applause": "APPLAUSE",
        "done": "DONE",
        "jiayou": "JIAYI",
    }

    @staticmethod
    def format_message(content: str) -> dict[str, Any]:
        """Convert markdown-like content to Feishu post format.

        Args:
            content: Raw message content in markdown-like format

        Returns:
            Feishu post format dictionary
        """
        paragraphs = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if line.strip().startswith('```'):
                i, code_block = FeishuFormatter._parse_code_block(lines, i)
                if code_block:
                    paragraphs.append(code_block)
                continue

            # Handle horizontal rule
            if line.strip() == '---':
                paragraphs.append([{"tag": "hr"}])
                i += 1
                continue

            # Handle headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                # Headers become bold text with size based on level
                styles = ["bold"]
                if level <= 2:
                    styles.append("underline")
                paragraphs.append([{
                    "tag": "text",
                    "text": text + "\n",
                    "style": styles
                }])
                i += 1
                continue

            # Handle list items
            list_match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)$', line)
            if list_match:
                i, list_items = FeishuFormatter._parse_list(lines, i)
                if list_items:
                    paragraphs.extend(list_items)
                continue

            # Handle quote blocks
            if line.strip().startswith('>'):
                i, quote = FeishuFormatter._parse_quote(lines, i)
                if quote:
                    paragraphs.append(quote)
                continue

            # Regular paragraph with inline formatting
            if line.strip():
                elements = FeishuFormatter._parse_inline(line)
                if elements:
                    paragraphs.append(elements)

            i += 1

        # If no paragraphs, create a simple text one
        if not paragraphs:
            paragraphs = [[{"tag": "text", "text": content}]]

        return {
            "zh_cn": {
                "title": "",
                "content": paragraphs
            }
        }

    @staticmethod
    def _parse_code_block(lines: list[str], start: int) -> tuple[int, list[dict] | None]:
        """Parse a code block.

        Args:
            lines: All lines
            start: Starting line index

        Returns:
            (next_index, code_block_paragraph or None)
        """
        line = lines[start]
        language = line.strip()[3:].strip() or "text"

        code_lines = []
        i = start + 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code_lines.append(lines[i])
            i += 1

        if not code_lines:
            return i + 1, None

        code_content = '\n'.join(code_lines)

        # Map common language names to Feishu supported languages
        language_map = {
            "py": "PYTHON",
            "python": "PYTHON",
            "js": "JAVASCRIPT",
            "javascript": "JAVASCRIPT",
            "ts": "TYPESCRIPT",
            "typescript": "TYPESCRIPT",
            "java": "JAVA",
            "go": "GO",
            "golang": "GO",
            "c": "C",
            "cpp": "CPP",
            "c++": "CPP",
            "rs": "RUST",
            "rust": "RUST",
            "rb": "RUBY",
            "ruby": "RUBY",
            "php": "PHP",
            "swift": "SWIFT",
            "kt": "KOTLIN",
            "kotlin": "KOTLIN",
            "sh": "SHELL",
            "bash": "BASH",
            "shell": "SHELL",
            "sql": "SQL",
            "json": "JSON",
            "xml": "XML",
            "yaml": "YAML",
            "yml": "YAML",
            "html": "HTML",
            "css": "CSS",
            "md": "MARKDOWN",
            "markdown": "MARKDOWN",
        }

        feishu_lang = language_map.get(language.lower(), "TEXT")

        return i + 1, [{
            "tag": "code_block",
            "language": feishu_lang,
            "text": code_content
        }]

    @staticmethod
    def _parse_list(lines: list[str], start: int) -> tuple[int, list[list[dict]]]:
        """Parse a list (ordered or unordered).

        Args:
            lines: All lines
            start: Starting line index

        Returns:
            (next_index, list_paragraphs)
        """
        paragraphs = []
        i = start

        while i < len(lines):
            line = lines[i]
            match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)$', line)

            if not match:
                break

            indent = len(match.group(1))
            marker = match.group(2)
            text = match.group(3)

            # Determine list level (0, 1, 2, etc. based on indent)
            level = indent // 2

            # Add bullet/number prefix
            if marker in ('-', '*'):
                prefix = "  " * level + "• "
            else:
                # Extract number for ordered list
                num = marker.rstrip('.')
                prefix = "  " * level + f"{num}. "

            # Parse inline formatting in list item
            elements = FeishuFormatter._parse_inline(prefix + text)
            if elements:
                paragraphs.append(elements)

            i += 1

        return i, paragraphs

    @staticmethod
    def _parse_quote(lines: list[str], start: int) -> tuple[int, list[dict] | None]:
        """Parse a quote block.

        Args:
            lines: All lines
            start: Starting line index

        Returns:
            (next_index, quote_paragraph or None)
        """
        quote_lines = []
        i = start

        while i < len(lines) and lines[i].strip().startswith('>'):
            line = lines[i].strip()
            # Remove leading > and space
            content = line[1:].strip() if len(line) > 1 else ""
            quote_lines.append(content)
            i += 1

        if not quote_lines:
            return i, None

        quote_text = '\n'.join(quote_lines)

        # Quote becomes italic text with > prefix
        return i, [{
            "tag": "text",
            "text": "> " + quote_text,
            "style": ["italic"]
        }]

    @staticmethod
    def _parse_inline(text: str) -> list[dict]:
        """Parse inline markdown elements.

        Supports:
        - **bold** or __bold__
        - *italic* or _italic_
        - ***bold+italic***
        - `code`
        - [text](url) links
        - <@user_id> mentions

        Args:
            text: Line of text

        Returns:
            List of Feishu elements
        """
        elements = []
        remaining = text

        # Pattern definitions (order matters - more specific first)
        patterns = [
            # Bold + italic
            (r'\*\*\*(.+?)\*\*\*', 'bold_italic'),
            (r'___(.+?)___', 'bold_italic'),
            # Bold
            (r'\*\*(.+?)\*\*', 'bold'),
            (r'__(.+?)__', 'bold'),
            # Italic
            (r'\*(.+?)\*', 'italic'),
            (r'_(.+?)_', 'italic'),
            # Code inline
            (r'`(.+?)`', 'code'),
            # Link [text](url)
            (r'\[([^\]]+)\]\(([^)]+)\)', 'link'),
            # @ mention <@user_id>
            (r'<@([^>]+)>', 'at'),
        ]

        while remaining:
            found = False

            for pattern, style in patterns:
                match = re.match(pattern, remaining)
                if match:
                    if style == 'link':
                        elements.append({
                            "tag": "a",
                            "href": match.group(2),
                            "text": match.group(1)
                        })
                    elif style == 'at':
                        elements.append({
                            "tag": "at",
                            "user_id": match.group(1)
                        })
                    elif style == 'code':
                        # Code inline - use text with lineThrough as code style
                        elements.append({
                            "tag": "text",
                            "text": match.group(1),
                            "style": ["lineThrough"]  # Best approximation for code
                        })
                    elif style == 'bold_italic':
                        elements.append({
                            "tag": "text",
                            "text": match.group(1),
                            "style": ["bold", "italic"]
                        })
                    else:
                        elements.append({
                            "tag": "text",
                            "text": match.group(1),
                            "style": [style]
                        })

                    remaining = remaining[match.end():]
                    found = True
                    break

            if not found:
                # Find next special character
                next_special = len(remaining)
                for pattern, _ in patterns:
                    match = re.search(pattern, remaining)
                    if match and match.start() < next_special:
                        next_special = match.start()

                if next_special > 0:
                    elements.append({
                        "tag": "text",
                        "text": remaining[:next_special]
                    })
                    remaining = remaining[next_special:]
                else:
                    # No more patterns, add rest as plain text
                    elements.append({
                        "tag": "text",
                        "text": remaining
                    })
                    break

        return elements

    @staticmethod
    def create_text_message(content: str) -> dict[str, Any]:
        """Create a simple text message.

        Args:
            content: Text content

        Returns:
            Feishu text format
        """
        return {
            "text": content
        }

    @staticmethod
    def create_card_message(
        title: str,
        content: str,
        color: str = "blue"
    ) -> dict[str, Any]:
        """Create an interactive card message.

        Args:
            title: Card title
            content: Card content (markdown supported)
            color: Header color (blue, green, red, etc.)

        Returns:
            Feishu card format
        """
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }
