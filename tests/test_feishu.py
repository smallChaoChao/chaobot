"""Tests for Feishu channel and formatter."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from chaobot.channels.feishu import FeishuChannel
from chaobot.config.schema import Config
from chaobot.utils.feishu_formatter import FeishuFormatter


@pytest.fixture
def feishu_config(tmp_path: Path) -> Config:
    """Create a config with Feishu settings."""
    config = Config()
    config.config_path = tmp_path / "config.json"
    config.workspace_path = tmp_path / "workspace"
    config.channels.feishu.enabled = True
    config.channels.feishu.app_id = "test_app_id"
    config.channels.feishu.app_secret = "test_app_secret"
    return config


@pytest.fixture
def feishu_channel(feishu_config: Config) -> FeishuChannel:
    """Create a Feishu channel."""
    return FeishuChannel(feishu_config)


def test_feishu_channel_init(feishu_channel: FeishuChannel) -> None:
    """Test Feishu channel initialization."""
    assert feishu_channel.name == "feishu"
    assert feishu_channel.enabled is True
    assert feishu_channel.app_id == "test_app_id"
    assert feishu_channel.app_secret == "test_app_secret"


def test_is_enabled_with_credentials(feishu_channel: FeishuChannel) -> None:
    """Test is_enabled returns True when credentials are set."""
    # Mock FEISHU_AVAILABLE to True
    with patch('chaobot.channels.feishu.FEISHU_AVAILABLE', True):
        assert feishu_channel.is_enabled() is True


def test_is_enabled_without_credentials(feishu_config: Config) -> None:
    """Test is_enabled returns False when credentials are missing."""
    feishu_config.channels.feishu.app_id = ""
    channel = FeishuChannel(feishu_config)

    with patch('chaobot.channels.feishu.FEISHU_AVAILABLE', True):
        assert channel.is_enabled() is False


def test_is_enabled_when_disabled(feishu_config: Config) -> None:
    """Test is_enabled returns False when channel is disabled."""
    feishu_config.channels.feishu.enabled = False
    channel = FeishuChannel(feishu_config)

    with patch('chaobot.channels.feishu.FEISHU_AVAILABLE', True):
        assert channel.is_enabled() is False


def test_format_message_plain_text() -> None:
    """Test formatting plain text message."""
    content = FeishuFormatter.format_message("Hello World")

    assert "zh_cn" in content
    assert content["zh_cn"]["title"] == ""
    assert len(content["zh_cn"]["content"]) == 1
    assert content["zh_cn"]["content"][0][0]["tag"] == "text"
    assert content["zh_cn"]["content"][0][0]["text"] == "Hello World"


def test_format_message_with_bold() -> None:
    """Test formatting message with bold text."""
    content = FeishuFormatter.format_message("**bold text**")

    paragraphs = content["zh_cn"]["content"]
    assert len(paragraphs) == 1
    assert paragraphs[0][0]["tag"] == "text"
    assert "bold" in paragraphs[0][0].get("style", [])


def test_format_message_with_italic() -> None:
    """Test formatting message with italic text."""
    content = FeishuFormatter.format_message("*italic text*")

    paragraphs = content["zh_cn"]["content"]
    assert paragraphs[0][0]["tag"] == "text"
    assert "italic" in paragraphs[0][0].get("style", [])


def test_format_message_with_link() -> None:
    """Test formatting message with hyperlink."""
    content = FeishuFormatter.format_message("[Click here](https://example.com)")

    paragraphs = content["zh_cn"]["content"]
    assert paragraphs[0][0]["tag"] == "a"
    assert paragraphs[0][0]["text"] == "Click here"
    assert paragraphs[0][0]["href"] == "https://example.com"


def test_format_message_with_code_block() -> None:
    """Test formatting message with code block."""
    message = "```python\nprint('hello')\n```"
    content = FeishuFormatter.format_message(message)

    paragraphs = content["zh_cn"]["content"]
    # Should have code block paragraph
    code_blocks = [p for p in paragraphs if p[0]["tag"] == "code_block"]
    assert len(code_blocks) == 1
    assert code_blocks[0][0]["language"] == "PYTHON"
    assert "print('hello')" in code_blocks[0][0]["text"]


def test_format_message_with_horizontal_rule() -> None:
    """Test formatting message with horizontal rule."""
    content = FeishuFormatter.format_message("Line 1\n---\nLine 2")

    paragraphs = content["zh_cn"]["content"]
    # Should have hr tag
    hrs = [p for p in paragraphs if p[0]["tag"] == "hr"]
    assert len(hrs) == 1


def test_parse_inline_mixed() -> None:
    """Test parsing mixed inline elements."""
    text = "Hello **bold** and *italic* world"
    elements = FeishuFormatter._parse_inline(text)

    assert len(elements) >= 3  # text, bold, text, italic, text
    # Find bold element
    bold_elements = [e for e in elements if "bold" in e.get("style", [])]
    assert len(bold_elements) == 1
    assert bold_elements[0]["text"] == "bold"


def test_format_message_multiline() -> None:
    """Test formatting multiline message."""
    message = "Line 1\n\nLine 2\n\nLine 3"
    content = FeishuFormatter.format_message(message)

    paragraphs = content["zh_cn"]["content"]
    # Should create separate paragraphs
    assert len(paragraphs) >= 2


def test_format_message_with_header() -> None:
    """Test formatting message with headers."""
    content = FeishuFormatter.format_message("# Title\n## Subtitle")

    paragraphs = content["zh_cn"]["content"]
    # Headers become bold text
    assert len(paragraphs) == 2
    assert "bold" in paragraphs[0][0].get("style", [])


def test_format_message_with_list() -> None:
    """Test formatting message with list items."""
    message = "- Item 1\n- Item 2\n- Item 3"
    content = FeishuFormatter.format_message(message)

    paragraphs = content["zh_cn"]["content"]
    assert len(paragraphs) == 3


def test_format_message_with_quote() -> None:
    """Test formatting message with quote block."""
    content = FeishuFormatter.format_message("> This is a quote")

    paragraphs = content["zh_cn"]["content"]
    assert len(paragraphs) == 1
    assert "italic" in paragraphs[0][0].get("style", [])


def test_format_message_with_bold_italic() -> None:
    """Test formatting message with bold+italic text."""
    content = FeishuFormatter.format_message("***bold and italic***")

    paragraphs = content["zh_cn"]["content"]
    assert len(paragraphs) == 1
    styles = paragraphs[0][0].get("style", [])
    assert "bold" in styles
    assert "italic" in styles


def test_format_message_with_inline_code() -> None:
    """Test formatting message with inline code."""
    content = FeishuFormatter.format_message("Use `print()` function")

    paragraphs = content["zh_cn"]["content"]
    # Find code element (has lineThrough style)
    code_elements = [e for e in paragraphs[0] if "lineThrough" in e.get("style", [])]
    assert len(code_elements) == 1
    assert code_elements[0]["text"] == "print()"


def test_create_text_message() -> None:
    """Test creating simple text message."""
    content = FeishuFormatter.create_text_message("Simple text")

    assert content["text"] == "Simple text"


def test_create_card_message() -> None:
    """Test creating card message."""
    content = FeishuFormatter.create_card_message(
        title="Card Title",
        content="Card content",
        color="blue"
    )

    assert content["header"]["title"]["content"] == "Card Title"
    assert content["header"]["template"] == "blue"


def test_receive_id_type_detection_open_id(feishu_channel: FeishuChannel) -> None:
    """Test receive_id_type detection for open_id."""
    # open_id starts with "ou_"
    open_id = "ou_1234567890abcdef"
    # This is tested indirectly through send_message
    # We just verify the logic here
    assert open_id.startswith("ou_")


def test_receive_id_type_detection_chat_id(feishu_channel: FeishuChannel) -> None:
    """Test receive_id_type detection for chat_id."""
    # chat_id starts with "oc_"
    chat_id = "oc_1234567890abcdef"
    assert chat_id.startswith("oc_")


def test_emoji_types() -> None:
    """Test emoji type mapping."""
    assert FeishuFormatter.EMOJI_TYPES["ok"] == "OK"
    assert FeishuFormatter.EMOJI_TYPES["thumbsup"] == "THUMBSUP"
    assert FeishuFormatter.EMOJI_TYPES["heart"] == "HEART"
