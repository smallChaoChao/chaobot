---
name: tavily-search
description: "Search the web using Tavily AI search API for accurate and up-to-date information"
homepage: https://tavily.com
metadata: {"chaobot":{"emoji":"🔍","requires":{"env":["TAVILY_API_KEY"]}}}
---

# Tavily Search Skill

Search the web using Tavily's AI-powered search API. Tavily provides accurate, up-to-date information from multiple sources.

## Setup

Set your Tavily API key:
```bash
export TAVILY_API_KEY="tvly-..."
```

Get a free API key at https://tavily.com

## Usage

### Basic Search

Search for any topic:
```python
tavily_search(query="latest AI developments 2024")
```

### Advanced Search

Search with specific parameters:
```python
tavily_search(
    query="climate change effects",
    search_depth="advanced",  # basic or advanced
    include_domains=["bbc.com", "reuters.com"],
    exclude_domains=["wikipedia.org"],
    max_results=10
)
```

### Search Parameters

- `query` (required): Search query string
- `search_depth`: "basic" (fast) or "advanced" (comprehensive)
- `include_domains`: List of domains to include
- `exclude_domains`: List of domains to exclude
- `max_results`: Maximum results (1-20)
- `include_answer`: Include AI-generated answer (true/false)
- `include_raw_content`: Include full page content (true/false)

## Examples

**Current news:**
```python
tavily_search(query="杭州今天天气", search_depth="basic")
```

**Research query:**
```python
tavily_search(
    query="quantum computing breakthroughs 2024",
    search_depth="advanced",
    max_results=10,
    include_answer=True
)
```

**Technical documentation:**
```python
tavily_search(
    query="Python asyncio best practices",
    include_domains=["docs.python.org", "realpython.com"]
)
```

## Response Format

```json
{
  "query": "search query",
  "results": [
    {
      "title": "Result title",
      "url": "https://example.com",
      "content": "Snippet or full content",
      "score": 0.95
    }
  ],
  "answer": "AI-generated summary (if requested)"
}
```

## Rate Limits

- Free tier: 1,000 requests/month
- Paid tiers: Higher limits available

Always check if Tavily search is available before using it. If the API key is not set, fall back to web_search tool.
