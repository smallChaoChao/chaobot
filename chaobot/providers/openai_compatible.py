"""OpenAI-compatible provider implementation."""

import asyncio
import json
from typing import Any, AsyncIterator

import httpx

from chaobot.providers.base import BaseProvider
from chaobot.providers.spec import ProviderSpec
from chaobot.utils.rate_limiter import get_rate_limiter


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI-compatible APIs."""

    def __init__(
        self,
        config: Any,
        provider_config: Any,
        spec: ProviderSpec
    ) -> None:
        """Initialize provider.

        Args:
            config: Application configuration
            provider_config: Provider-specific configuration
            spec: Provider specification
        """
        super().__init__(config, provider_config)
        self.spec = spec
        self.api_key = provider_config.api_key
        self.api_base = provider_config.api_base or spec.api_base
        self.timeout = provider_config.timeout
        self.rate_limit_rpm = getattr(provider_config, 'rate_limit_rpm', None)

    async def complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Complete a conversation with retry logic.

        Args:
            messages: List of messages

        Returns:
            Response dictionary
        """
        if not self.api_key:
            return {
                "content": f"Error: No API key configured for {self.spec.display_name}",
                "tool_calls": None
            }

        formatted_messages = self.format_messages(messages)
        model = self.config.agents.defaults.model

        # Remove provider prefix from model name if present
        if "/" in model and model.split("/")[0] == self.spec.name:
            model = model.split("/", 1)[1]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": self.config.agents.defaults.temperature,
            "max_tokens": self.config.agents.defaults.max_tokens
        }

        # Add tools if supported
        # Note: Some providers (like Aliyun DashScope) may not fully support OpenAI-compatible tool format
        # Only add tools if explicitly supported and not using custom API base
        if self.spec.supports_tools:
            tools = self._extract_tools(messages)
            if tools:
                # Check if using Aliyun DashScope (either via aliyun provider or custom api_base)
                api_base = self.api_base or ""
                is_aliyun = "aliyun" in api_base.lower() or "dashscope" in api_base.lower()
                
                if is_aliyun:
                    # Aliyun DashScope doesn't support standard OpenAI tool format via compatible-mode API
                    # Skip tools to avoid 400 Bad Request error
                    pass
                else:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

        # Apply rate limiting before making request
        rate_limiter = get_rate_limiter()
        await rate_limiter.acquire(self.spec.name, self.rate_limit_rpm)

        # Retry logic
        max_retries = self.provider_config.max_retries
        retry_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    data = response.json()

                    return self._parse_response(data)

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors (client errors)
                if e.response.status_code < 500:
                    return {
                        "content": f"HTTP error {e.response.status_code}: {e}",
                        "tool_calls": None
                    }
                # Retry on 5xx errors (server errors)
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return {
                    "content": f"HTTP error after {max_retries} retries: {e}",
                    "tool_calls": None
                }
            except httpx.NetworkError as e:
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return {
                    "content": f"Network error after {max_retries} retries: {e}",
                    "tool_calls": None
                }
            except Exception as e:
                import traceback
                error_msg = str(e) if str(e) else type(e).__name__
                tb = traceback.format_exc()
                return {
                    "content": f"Error: {error_msg}\n\nTraceback:\n{tb}",
                    "tool_calls": None
                }

        return {
            "content": "Error: Max retries exceeded",
            "tool_calls": None
        }

    async def complete_stream(
        self,
        messages: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Complete a conversation with streaming.

        Args:
            messages: List of messages

        Yields:
            Chunks of response content
        """
        if not self.api_key:
            yield f"Error: No API key configured for {self.spec.display_name}"
            return

        formatted_messages = self.format_messages(messages)
        model = self.config.agents.defaults.model

        # Remove provider prefix from model name if present
        if "/" in model and model.split("/")[0] == self.spec.name:
            model = model.split("/", 1)[1]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": self.config.agents.defaults.temperature,
            "max_tokens": self.config.agents.defaults.max_tokens,
            "stream": True
        }

        # Apply rate limiting before making request
        rate_limiter = get_rate_limiter()
        await rate_limiter.acquire(self.spec.name, self.rate_limit_rpm)

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPError as e:
            yield f"HTTP error: {e}"
        except Exception as e:
            yield f"Error: {e}"

    def format_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format messages for OpenAI-compatible API.

        Args:
            messages: Generic messages

        Returns:
            OpenAI-formatted messages
        """
        formatted = []

        for msg in messages:
            formatted_msg = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }

            # Handle tool calls and results
            if "tool_calls" in msg:
                # Convert tool_calls to OpenAI format
                formatted_tool_calls = []
                for tc in msg["tool_calls"]:
                    formatted_tc = {
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": json.dumps(tc.get("arguments", {})) if isinstance(tc.get("arguments"), dict) else tc.get("arguments", "{}")
                        }
                    }
                    formatted_tool_calls.append(formatted_tc)
                formatted_msg["tool_calls"] = formatted_tool_calls
            if "tool_call_id" in msg:
                formatted_msg["tool_call_id"] = msg["tool_call_id"]
            if "name" in msg:
                formatted_msg["name"] = msg["name"]

            formatted.append(formatted_msg)

        return formatted

    def _extract_tools(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]] | None:
        """Extract tool definitions from messages.

        Args:
            messages: List of messages

        Returns:
            Tool definitions or None
        """
        # Tools are typically passed in the first message's metadata
        # This is a simplified implementation
        for msg in messages:
            if msg.get("role") == "system" and "tools" in msg:
                return msg["tools"]
        return None

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse OpenAI-compatible response.

        Args:
            data: Response data

        Returns:
            Standardized response
        """
        if "choices" not in data or not data["choices"]:
            return {
                "content": "Error: Empty response from API",
                "tool_calls": None
            }

        choice = data["choices"][0]
        message = choice.get("message", {})

        content = message.get("content", "")
        tool_calls = None

        # Check for standard tool_calls format
        if "tool_calls" in message:
            tool_calls = []
            for tc in message["tool_calls"]:
                args = tc.get("function", {}).get("arguments", "{}")
                # Parse arguments if it's a string (JSON)
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": args
                })
        # Check for XML-style tool call in content (some providers like qwen)
        elif content and "<tool_call>" in content:
            import re
            tool_calls = []

            # Try format 1: JSON inside XML
            pattern1 = r'<tool_call>\s*\{[^}]*"name"\s*:\s*"([^"]*)"[^}]*"arguments"\s*:\s*(\{[^}]*\})[^}]*\}\s*</tool_call>'
            matches1 = re.findall(pattern1, content, re.DOTALL)
            for name, args_str in matches1:
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append({
                    "id": f"call_{hash(name + args_str) & 0xFFFFFFFF}",
                    "name": name,
                    "arguments": args
                })

            # Try format 2: <function=name> with <parameter> tags
            # Pattern: <function=func_name><parameter=param_name>value</parameter></function>
            pattern2 = r'<tool_call>\s*<function=(\w+)>\s*(.*?)</function>\s*</tool_call>'
            matches2 = re.findall(pattern2, content, re.DOTALL)
            for name, params_xml in matches2:
                args = {}
                # Parse parameters: <parameter=param_name>value</parameter>
                param_pattern = r'<parameter=(\w+)>(.*?)</parameter>'
                for param_name, param_value in re.findall(param_pattern, params_xml, re.DOTALL):
                    args[param_name] = param_value.strip()

                if args:
                    tool_calls.append({
                        "id": f"call_{hash(name + str(args)) & 0xFFFFFFFF}",
                        "name": name,
                        "arguments": args
                    })

            # Remove tool call XML from content
            content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL).strip()

        # Check for <tool> format (alternative XML format)
        if not tool_calls and content and "<tool>" in content:
            import re
            tool_calls = []

            # Pattern: <tool><name>tool_name</name><parameter=key>value</parameter></tool>
            pattern = r'<tool>\s*<name>(\w+)</name>\s*(.*?)</tool>'
            matches = re.findall(pattern, content, re.DOTALL)
            for name, params_xml in matches:
                args = {}
                # Parse parameters: <parameter=key>value</parameter>
                param_pattern = r'<parameter=(\w+)>(.*?)</parameter>'
                for param_name, param_value in re.findall(param_pattern, params_xml, re.DOTALL):
                    args[param_name] = param_value.strip()

                if args:
                    tool_calls.append({
                        "id": f"call_{hash(name + str(args)) & 0xFFFFFFFF}",
                        "name": name,
                        "arguments": args
                    })

            # Remove tool XML from content
            content = re.sub(r'<tool>.*?</tool>', '', content, flags=re.DOTALL).strip()

        # Check for <tool_name> format (e.g., <file_read>, <shell>, etc.)
        if not tool_calls and content:
            import re
            # Pattern: <tool_name>arguments</tool_name> or <tool_name arg="value"/>
            # Try pattern: <tool_name>value</tool_name>
            pattern1 = r'<(\w+)>([^<]+)</\1>'
            matches1 = re.findall(pattern1, content, re.DOTALL)
            for name, arg_value in matches1:
                # Check if this looks like a tool name (file_read, shell, web_search, etc.)
                if name in ['file_read', 'file_write', 'file_edit', 'shell', 'web_search', 'web_fetch', 'browser_screenshot']:
                    if not tool_calls:
                        tool_calls = []
                    # Single argument tools
                    if name == 'file_read':
                        tool_calls.append({
                            "id": f"call_{hash(name + arg_value) & 0xFFFFFFFF}",
                            "name": name,
                            "arguments": {"path": arg_value.strip()}
                        })
                    elif name == 'shell':
                        tool_calls.append({
                            "id": f"call_{hash(name + arg_value) & 0xFFFFFFFF}",
                            "name": name,
                            "arguments": {"command": arg_value.strip()}
                        })
                    elif name in ['web_search', 'web_fetch']:
                        tool_calls.append({
                            "id": f"call_{hash(name + arg_value) & 0xFFFFFFFF}",
                            "name": name,
                            "arguments": {"query" if name == 'web_search' else "url": arg_value.strip()}
                        })

            if tool_calls:
                # Remove tool XML from content
                for name, _ in matches1:
                    if name in ['file_read', 'file_write', 'file_edit', 'shell', 'web_search', 'web_fetch', 'browser_screenshot']:
                        content = re.sub(rf'<{name}>.*?</{name}>', '', content, flags=re.DOTALL).strip()

        # Check for nested format: <tool_name><command>value</command></tool_name>
        if not tool_calls and content:
            import re
            # Pattern: <shell><command>value</command></shell>
            pattern2 = r'<(shell|file_read|web_search|web_fetch)>\s*<(command|path|query|url)>(.*?)</\2>\s*</\1>'
            matches2 = re.findall(pattern2, content, re.DOTALL)
            for tool_name, arg_name, arg_value in matches2:
                if not tool_calls:
                    tool_calls = []
                
                # Map argument names
                arg_key_map = {
                    'command': 'command',
                    'path': 'path',
                    'query': 'query',
                    'url': 'url'
                }
                arg_key = arg_key_map.get(arg_name, arg_name)
                
                tool_calls.append({
                    "id": f"call_{hash(tool_name + arg_value) & 0xFFFFFFFF}",
                    "name": tool_name,
                    "arguments": {arg_key: arg_value.strip()}
                })
            
            if tool_calls:
                # Remove nested tool XML from content
                for tool_name, arg_name, _ in matches2:
                    content = re.sub(rf'<{tool_name}>\s*<{arg_name}>.*?</{arg_name}>\s*</{tool_name}>', '', content, flags=re.DOTALL).strip()

        return {
            "content": content or "",
            "tool_calls": tool_calls
        }
