"""OpenAI-compatible provider implementation."""

import asyncio
import json
from typing import Any, AsyncIterator

import httpx

from chaobot.providers.base import BaseProvider
from chaobot.providers.spec import ProviderSpec


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
        if self.spec.supports_tools:
            tools = self._extract_tools(messages)
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

        # Retry logic
        max_retries = self.provider_config.max_retries
        retry_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload
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
                return {
                    "content": f"Error: {e}",
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
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
                formatted_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                formatted_msg["tool_call_id"] = msg["tool_call_id"]

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

        return {
            "content": content or "",
            "tool_calls": tool_calls
        }
