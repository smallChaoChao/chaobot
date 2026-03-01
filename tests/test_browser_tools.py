"""Tests for browser automation tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chaobot.agent.tools.browser import (
    BrowserManager,
    BrowserNavigateTool,
    BrowserClickTool,
    BrowserInputTool,
    BrowserScreenshotTool,
    BrowserGetHtmlTool,
    BrowserScrollTool,
    BrowserFindElementTool,
)
from chaobot.config.schema import Config


@pytest.fixture
def config() -> Config:
    """Create test config."""
    return Config()


@pytest.fixture
def mock_page():
    """Create mock Playwright page."""
    page = AsyncMock()
    page.title = AsyncMock(return_value="Test Page")
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.press = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.content = AsyncMock(return_value="<html><body>Test</body></html>")
    page.inner_html = AsyncMock(return_value="<div>Test</div>")
    page.evaluate = AsyncMock()
    page.query_selector = AsyncMock(return_value=AsyncMock())
    page.query_selector_all = AsyncMock(return_value=[])
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_context():
    """Create mock Playwright context."""
    context = AsyncMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_browser():
    """Create mock Playwright browser."""
    browser = AsyncMock()
    browser.close = AsyncMock()
    return browser


class TestBrowserManager:
    """Test BrowserManager singleton."""

    def test_singleton_pattern(self):
        """Test that BrowserManager is a singleton."""
        manager1 = BrowserManager()
        manager2 = BrowserManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_session_without_playwright(self):
        """Test getting session when playwright is not installed."""
        manager = BrowserManager()
        # Reset any existing sessions
        manager._sessions = {}
        
        # Mock import failure
        with patch.dict('sys.modules', {'playwright': None}):
            session = await manager.get_session("test")
            assert session.page is None


class TestBrowserNavigateTool:
    """Test BrowserNavigateTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserNavigateTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_navigate"
        assert "url" in definition["function"]["parameters"]["properties"]


class TestBrowserClickTool:
    """Test BrowserClickTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserClickTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_click"
        assert "selector" in definition["function"]["parameters"]["properties"]


class TestBrowserInputTool:
    """Test BrowserInputTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserInputTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_input"
        assert "selector" in definition["function"]["parameters"]["properties"]
        assert "text" in definition["function"]["parameters"]["properties"]
        assert "submit" in definition["function"]["parameters"]["properties"]


class TestBrowserScreenshotTool:
    """Test BrowserScreenshotTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserScreenshotTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_screenshot"
        assert "full_page" in definition["function"]["parameters"]["properties"]


class TestBrowserGetHtmlTool:
    """Test BrowserGetHtmlTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserGetHtmlTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_get_html"
        assert "selector" in definition["function"]["parameters"]["properties"]


class TestBrowserScrollTool:
    """Test BrowserScrollTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserScrollTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_scroll"
        assert "direction" in definition["function"]["parameters"]["properties"]
        assert "up" in definition["function"]["parameters"]["properties"]["direction"]["enum"]
        assert "down" in definition["function"]["parameters"]["properties"]["direction"]["enum"]
        assert "to" in definition["function"]["parameters"]["properties"]["direction"]["enum"]


class TestBrowserFindElementTool:
    """Test BrowserFindElementTool."""

    @pytest.mark.asyncio
    async def test_get_definition(self, config: Config):
        """Test tool definition."""
        tool = BrowserFindElementTool(config)
        definition = tool.get_definition()
        
        assert definition["function"]["name"] == "browser_find_element"
        assert "selector" in definition["function"]["parameters"]["properties"]
        assert "max_results" in definition["function"]["parameters"]["properties"]
