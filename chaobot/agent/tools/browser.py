"""Browser automation tools using Playwright."""

import base64
from dataclasses import dataclass
from typing import Any

from chaobot.agent.tools.base import BaseTool, ToolResult


@dataclass
class BrowserSession:
    """Browser session state."""

    page: Any = None
    context: Any = None
    browser: Any = None


class BrowserManager:
    """Manages browser instances and sessions."""

    _instance = None
    _sessions: dict[str, BrowserSession] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_session(self, session_id: str = "default") -> BrowserSession:
        """Get or create browser session.

        Args:
            session_id: Session identifier

        Returns:
            Browser session
        """
        if session_id not in self._sessions:
            try:
                from playwright.async_api import async_playwright

                self._playwright = await async_playwright().start()
                browser = await self._playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()

                session = BrowserSession(
                    page=page,
                    context=context,
                    browser=browser
                )
                self._sessions[session_id] = session
            except ImportError:
                return BrowserSession()

        return self._sessions[session_id]

    async def close_session(self, session_id: str = "default") -> None:
        """Close browser session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if session.page:
                await session.page.close()
            if session.context:
                await session.context.close()
            if session.browser:
                await session.browser.close()
            del self._sessions[session_id]


class BrowserNavigateTool(BaseTool):
    """Navigate to a URL."""

    name = "browser_navigate"
    description = "Navigate the browser to a specified URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to navigate to"
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": ["url"]
    }

    async def execute(self, url: str, session_id: str = "default", **kwargs) -> ToolResult:
        """Navigate to URL.

        Args:
            url: URL to navigate to
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available. Please install playwright: pip install playwright"
                )

            await session.page.goto(url, wait_until="networkidle")
            title = await session.page.title()

            return ToolResult(
                success=True,
                content=f"Navigated to {url}\nPage title: {title}",
                data={"url": url, "title": title}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to navigate: {str(e)}"
            )


class BrowserClickTool(BaseTool):
    """Click on an element."""

    name = "browser_click"
    description = "Click on an element by selector"
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector or XPath of the element to click"
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": ["selector"]
    }

    async def execute(self, selector: str, session_id: str = "default", **kwargs) -> ToolResult:
        """Click on element.

        Args:
            selector: CSS selector or XPath
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            await session.page.click(selector)

            return ToolResult(
                success=True,
                content=f"Clicked on element: {selector}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to click: {str(e)}"
            )


class BrowserInputTool(BaseTool):
    """Input text into a form field."""

    name = "browser_input"
    description = "Input text into a form field"
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector of the input field"
            },
            "text": {
                "type": "string",
                "description": "Text to input"
            },
            "submit": {
                "type": "boolean",
                "description": "Whether to submit the form after input",
                "default": False
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": ["selector", "text"]
    }

    async def execute(self, selector: str, text: str, submit: bool = False,
                     session_id: str = "default", **kwargs) -> ToolResult:
        """Input text into field.

        Args:
            selector: CSS selector of input field
            text: Text to input
            submit: Whether to submit form
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            await session.page.fill(selector, text)

            if submit:
                await session.page.press(selector, "Enter")

            return ToolResult(
                success=True,
                content=f"Input '{text}' into {selector}" + (" and submitted" if submit else "")
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to input: {str(e)}"
            )


class BrowserScreenshotTool(BaseTool):
    """Take a screenshot of the current page."""

    name = "browser_screenshot"
    description = "Take a screenshot of the current page"
    parameters = {
        "type": "object",
        "properties": {
            "full_page": {
                "type": "boolean",
                "description": "Whether to capture full page or just viewport",
                "default": False
            },
            "selector": {
                "type": "string",
                "description": "CSS selector of specific element to capture (optional)"
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": []
    }

    async def execute(self, full_page: bool = False, selector: str | None = None,
                     session_id: str = "default", **kwargs) -> ToolResult:
        """Take screenshot.

        Args:
            full_page: Capture full page
            selector: Specific element selector
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            if selector:
                element = await session.page.query_selector(selector)
                if not element:
                    return ToolResult(
                        success=False,
                        content=f"Element not found: {selector}"
                    )
                screenshot_bytes = await element.screenshot()
            else:
                screenshot_bytes = await session.page.screenshot(full_page=full_page)

            # Convert to base64 for display
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

            return ToolResult(
                success=True,
                content=f"Screenshot captured ({len(screenshot_bytes)} bytes)",
                data={
                    "screenshot_base64": screenshot_b64,
                    "format": "png"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to take screenshot: {str(e)}"
            )


class BrowserGetHtmlTool(BaseTool):
    """Get the HTML content of the current page."""

    name = "browser_get_html"
    description = "Get the HTML content of the current page"
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector of specific element to get HTML from (optional)"
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": []
    }

    async def execute(self, selector: str | None = None, session_id: str = "default",
                     **kwargs) -> ToolResult:
        """Get page HTML.

        Args:
            selector: Specific element selector
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            if selector:
                element = await session.page.query_selector(selector)
                if not element:
                    return ToolResult(
                        success=False,
                        content=f"Element not found: {selector}"
                    )
                html = await element.inner_html()
            else:
                html = await session.page.content()

            # Truncate if too long
            if len(html) > 10000:
                html = html[:10000] + "\n... (truncated)"

            return ToolResult(
                success=True,
                content=f"HTML content ({len(html)} characters):\n\n{html}",
                data={"html": html}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to get HTML: {str(e)}"
            )


class BrowserScrollTool(BaseTool):
    """Scroll the page."""

    name = "browser_scroll"
    description = "Scroll the page up, down, or to a specific element"
    parameters = {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "description": "Direction to scroll: up, down, or to element",
                "enum": ["up", "down", "to"]
            },
            "amount": {
                "type": "integer",
                "description": "Pixels to scroll (for up/down)",
                "default": 500
            },
            "selector": {
                "type": "string",
                "description": "CSS selector of element to scroll to (for 'to' direction)"
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": ["direction"]
    }

    async def execute(self, direction: str, amount: int = 500, selector: str | None = None,
                     session_id: str = "default", **kwargs) -> ToolResult:
        """Scroll page.

        Args:
            direction: Scroll direction
            amount: Pixels to scroll
            selector: Element selector for 'to' direction
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            if direction == "up":
                await session.page.evaluate(f"window.scrollBy(0, -{amount})")
                msg = f"Scrolled up by {amount} pixels"
            elif direction == "down":
                await session.page.evaluate(f"window.scrollBy(0, {amount})")
                msg = f"Scrolled down by {amount} pixels"
            elif direction == "to":
                if not selector:
                    return ToolResult(
                        success=False,
                        content="Selector required for 'to' direction"
                    )
                element = await session.page.query_selector(selector)
                if not element:
                    return ToolResult(
                        success=False,
                        content=f"Element not found: {selector}"
                    )
                await element.scroll_into_view_if_needed()
                msg = f"Scrolled to element: {selector}"
            else:
                return ToolResult(
                    success=False,
                    content=f"Invalid direction: {direction}"
                )

            return ToolResult(
                success=True,
                content=msg
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to scroll: {str(e)}"
            )


class BrowserFindElementTool(BaseTool):
    """Find elements on the page."""

    name = "browser_find_element"
    description = "Find elements on the page and return their information"
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector to find elements"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10
            },
            "session_id": {
                "type": "string",
                "description": "Browser session ID (optional)",
                "default": "default"
            }
        },
        "required": ["selector"]
    }

    async def execute(self, selector: str, max_results: int = 10,
                     session_id: str = "default", **kwargs) -> ToolResult:
        """Find elements.

        Args:
            selector: CSS selector
            max_results: Maximum results
            session_id: Browser session ID

        Returns:
            Tool execution result
        """
        try:
            manager = BrowserManager()
            session = await manager.get_session(session_id)

            if not session.page:
                return ToolResult(
                    success=False,
                    content="Browser automation not available"
                )

            elements = await session.page.query_selector_all(selector)
            elements = elements[:max_results]

            results = []
            for i, element in enumerate(elements):
                try:
                    text = await element.inner_text()
                    tag = await element.evaluate("el => el.tagName")
                    visible = await element.is_visible()

                    results.append({
                        "index": i,
                        "tag": tag,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "visible": visible
                    })
                except:
                    continue

            return ToolResult(
                success=True,
                content=f"Found {len(results)} elements matching '{selector}':\n" +
                       "\n".join([f"[{r['index']}] <{r['tag']}> {r['text']}" for r in results]),
                data={"elements": results}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Failed to find elements: {str(e)}"
            )
