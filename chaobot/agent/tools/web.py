"""Web-related tools."""

import json
from typing import Any

import httpx

from chaobot.agent.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Search the web using Brave Search API or DuckDuckGo (fallback)."""

    name = "web_search"
    description = "Search the web for information using Brave Search API or DuckDuckGo"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (max 20)",
                "default": 5
            }
        },
        "required": ["query"]
    }

    BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
    DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search web using Brave Search API or DuckDuckGo as fallback.

        Args:
            **kwargs: Must contain 'query', optionally 'num_results'

        Returns:
            Tool execution result
        """
        query = kwargs.get("query", "")
        num_results = min(kwargs.get("num_results", 5), 20)  # Max 20 results

        if not query:
            return ToolResult(
                success=False,
                content="No query provided"
            )

        # Get API key from config
        api_key = getattr(self.config.tools, 'brave_api_key', None)

        # Try Brave Search if API key is configured
        if api_key:
            result = await self._search_brave(query, num_results, api_key)
            if result.success:
                return result

        # Fallback to DuckDuckGo
        return await self._search_duckduckgo(query, num_results)

    async def _search_brave(self, query: str, num_results: int, api_key: str) -> ToolResult:
        """Search using Brave Search API."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.BRAVE_API_URL,
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": api_key
                    },
                    params={
                        "q": query,
                        "count": num_results,
                        "offset": 0,
                        "mkt": "en-US",
                        "safesearch": "moderate",
                        "freshness": "all",
                        "text_decorations": False,
                        "text_snippets": True
                    }
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("web", {}).get("results", [])
                if not results:
                    return ToolResult(
                        success=False,
                        content=""
                    )

                formatted_results = []
                for i, result in enumerate(results[:num_results], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    description = result.get("description", "No description")
                    formatted_results.append(
                        f"{i}. {title}\n   URL: {url}\n   {description}\n"
                    )

                content = f"Search results for '{query}':\n\n"
                content += "\n".join(formatted_results)

                return ToolResult(
                    success=True,
                    content=content,
                    data={
                        "query": query,
                        "total_results": len(results),
                        "returned_results": len(formatted_results),
                        "provider": "brave"
                    }
                )

        except Exception:
            return ToolResult(
                success=False,
                content=""
            )

    async def _search_duckduckgo(self, query: str, num_results: int) -> ToolResult:
        """Search using DuckDuckGo (HTML version, no API key required)."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.DUCKDUCKGO_URL,
                    data={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                response.raise_for_status()
                html = response.text

                # Parse HTML results (simple regex-based parsing)
                import re
                results = []

                # Find result blocks
                result_blocks = re.findall(
                    r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>',
                    html,
                    re.DOTALL
                )

                for i, (url, title, snippet) in enumerate(result_blocks[:num_results], 1):
                    # Clean up HTML entities
                    title = title.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    snippet = snippet.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    results.append(f"{i}. {title}\n   URL: {url}\n   {snippet}\n")

                if not results:
                    return ToolResult(
                        success=False,
                        content="No results found or DuckDuckGo search failed."
                    )

                content = f"Search results for '{query}' (via DuckDuckGo):\n\n"
                content += "\n".join(results)

                return ToolResult(
                    success=True,
                    content=content,
                    data={
                        "query": query,
                        "returned_results": len(results),
                        "provider": "duckduckgo"
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Search failed: {e}"
            )


class WebFetchTool(BaseTool):
    """Fetch web page content."""

    name = "web_fetch"
    description = "Fetch and extract content from a web page"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch"
            }
        },
        "required": ["url"]
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Fetch web page.

        Args:
            **kwargs: Must contain 'url'

        Returns:
            Tool execution result
        """
        url = kwargs.get("url", "")

        if not url:
            return ToolResult(
                success=False,
                content="No URL provided"
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # TODO: Implement HTML to text extraction
                content = response.text[:5000]  # Limit content

                return ToolResult(
                    success=True,
                    content=f"Fetched {url}:\n\n{content[:2000]}...",
                    data={
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "content_length": len(response.text)
                    }
                )

        except httpx.HTTPError as e:
            return ToolResult(
                success=False,
                content=f"HTTP error fetching {url}: {e}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error fetching {url}: {e}"
            )
