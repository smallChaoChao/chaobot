"""LiteLLM-based provider implementation."""

import json
import os
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion

# Configure litellm to avoid RuntimeWarning
litellm.success_callback = []
litellm.failure_callback = []
litellm.callbacks = []

from chaobot.providers.base import BaseProvider


class LiteLLMProvider(BaseProvider):
    """Provider using LiteLLM for unified LLM access."""

    def __init__(
        self,
        config: Any,
        provider_config: Any,
        model: str = "openai/gpt-4o"
    ) -> None:
        """Initialize LiteLLM provider.

        Args:
            config: Application configuration
            provider_config: Provider-specific configuration
            model: Model name in liteLLM format (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
        """
        super().__init__(config, provider_config)
        self.model = model
        self._setup_env()

    def _setup_env(self) -> None:
        """Set up environment variables for LiteLLM based on provider config."""
        providers_config = self.config.providers

        if self.model.startswith("openrouter/"):
            if providers_config.openrouter.api_key:
                os.environ["OPENROUTER_API_KEY"] = providers_config.openrouter.api_key
            if providers_config.openrouter.api_base:
                os.environ["OPENROUTER_API_BASE"] = providers_config.openrouter.api_base

        elif self.model.startswith("anthropic/") or self.model.startswith("claude"):
            if providers_config.anthropic.api_key:
                os.environ["ANTHROPIC_API_KEY"] = providers_config.anthropic.api_key

        elif self.model.startswith("openai/"):
            if providers_config.openai.api_key:
                os.environ["OPENAI_API_KEY"] = providers_config.openai.api_key
            if providers_config.openai.api_base:
                os.environ["OPENAI_API_BASE"] = providers_config.openai.api_base

        elif self.model.startswith("deepseek/"):
            if providers_config.deepseek.api_key:
                os.environ["DEEPSEEK_API_KEY"] = providers_config.deepseek.api_key
            if providers_config.deepseek.api_base:
                os.environ["DEEPSEEK_API_BASE"] = providers_config.deepseek.api_base

        elif self.model.startswith("groq/"):
            if providers_config.groq.api_key:
                os.environ["GROQ_API_KEY"] = providers_config.groq.api_key

        elif self.model.startswith("gemini/"):
            if providers_config.gemini.api_key:
                os.environ["GEMINI_API_KEY"] = providers_config.gemini.api_key
        else:
            if providers_config.custom.api_key:
                os.environ["OPENAI_API_KEY"] = providers_config.custom.api_key
            if providers_config.custom.api_base:
                os.environ["OPENAI_API_BASE"] = providers_config.custom.api_base
            if providers_config.openai.api_key:
                os.environ["OPENAI_API_KEY"] = providers_config.openai.api_key
            if providers_config.openai.api_base:
                os.environ["OPENAI_API_BASE"] = providers_config.openai.api_base

    def _get_model_name(self) -> str:
        """Get the model name for LiteLLM.

        Returns:
            Model name in LiteLLM format
        """
        model = self.model

        if model.startswith("openrouter/"):
            return model
        elif model.startswith("anthropic/") or model.startswith("claude"):
            if not model.startswith("anthropic/"):
                return f"anthropic/{model}"
            return model
        elif model.startswith("openai/"):
            return model
        elif model.startswith("deepseek/"):
            return model
        elif model.startswith("groq/"):
            return model
        elif model.startswith("gemini/"):
            return model
        elif model.startswith("qwen") or model.startswith("qwen3"):
            return f"openai/{model}"
        else:
            return f"openai/{model}"

    async def complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Complete a conversation using LiteLLM.

        Args:
            messages: List of messages

        Returns:
            Response dictionary with 'content' and optionally 'tool_calls'
        """
        try:
            model = self._get_model_name()
            formatted_messages = self.format_messages(messages)

            kwargs: dict[str, Any] = {
                "model": model,
                "messages": formatted_messages,
                "temperature": self.config.agents.defaults.temperature,
            }

            if self.config.agents.defaults.max_tokens:
                kwargs["max_tokens"] = self.config.agents.defaults.max_tokens

            tools = self._extract_tools(messages)
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await acompletion(**kwargs)

            return self._parse_response(response)

        except Exception as e:
            import traceback
            error_msg = str(e) if str(e) else type(e).__name__
            tb = traceback.format_exc()
            return {
                "content": f"Error: {error_msg}\n\nTraceback:\n{tb}",
                "tool_calls": None
            }

    async def complete_stream(
        self,
        messages: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Complete a conversation with streaming using LiteLLM.

        Args:
            messages: List of messages

        Yields:
            Chunks of response content
        """
        try:
            model = self._get_model_name()
            formatted_messages = self.format_messages(messages)

            kwargs: dict[str, Any] = {
                "model": model,
                "messages": formatted_messages,
                "temperature": self.config.agents.defaults.temperature,
                "stream": True,
            }

            if self.config.agents.defaults.max_tokens:
                kwargs["max_tokens"] = self.config.agents.defaults.max_tokens

            response = await acompletion(**kwargs)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error: {e}"

    def format_messages(
        self,
        messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format messages for LiteLLM.

        Args:
            messages: Generic messages

        Returns:
            LiteLLM-formatted messages
        """
        formatted = []

        for msg in messages:
            formatted_msg = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }

            if "tool_calls" in msg:
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
        for msg in messages:
            if msg.get("role") == "system" and "tools" in msg:
                return msg["tools"]
        return None

    def _parse_response(self, response: Any) -> dict[str, Any]:
        """Parse LiteLLM response.

        Args:
            response: Raw LiteLLM response

        Returns:
            Standardized response dictionary
        """
        if not response or not response.choices:
            return {
                "content": "Error: Empty response from API",
                "tool_calls": None
            }

        choice = response.choices[0]
        message = choice.message

        content = message.content or ""
        tool_calls = None

        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args
                })

        elif content and self._has_xml_tool_call(content):
            tool_calls = self._parse_xml_tool_calls(content)
            if tool_calls:
                content = self._remove_xml_tool_calls(content)

        return {
            "content": content or "",
            "tool_calls": tool_calls
        }

    def _has_xml_tool_call(self, content: str) -> bool:
        """Check if content contains XML-style tool calls.

        Args:
            content: Response content

        Returns:
            True if XML tool calls detected
        """
        xml_patterns = ["<tool>", "<function=", "<file_read>", "<shell>", "<web_search>"]
        return any(pattern in content for pattern in xml_patterns)

    def _parse_xml_tool_calls(self, content: str) -> list[dict[str, Any]] | None:
        """Parse XML-style tool calls from content.

        Args:
            content: Response content

        Returns:
            List of tool calls or None
        """
        import re
        tool_calls = []

        pattern1 = r'<tool>\s*<name>(\w+)</name>\s*(.*?)</tool>'
        matches1 = re.findall(pattern1, content, re.DOTALL)
        for name, params_xml in matches1:
            args = {}
            param_pattern = r'<parameter=(\w+)>(.*?)</parameter>'
            for param_name, param_value in re.findall(param_pattern, params_xml, re.DOTALL):
                args[param_name] = param_value.strip()
            if args:
                tool_calls.append({
                    "id": f"call_{hash(name + str(args)) & 0xFFFFFFFF}",
                    "name": name,
                    "arguments": args
                })

        if not tool_calls:
            pattern2 = r'<function=(\w+)>\s*(.*?)</function>'
            matches2 = re.findall(pattern2, content, re.DOTALL)
            for name, params_xml in matches2:
                args = {}
                param_pattern = r'<parameter=(\w+)>(.*?)</parameter>'
                for param_name, param_value in re.findall(param_pattern, params_xml, re.DOTALL):
                    args[param_name] = param_value.strip()
                if args:
                    tool_calls.append({
                        "id": f"call_{hash(name + str(args)) & 0xFFFFFFFF}",
                        "name": name,
                        "arguments": args
                    })

        if not tool_calls:
            pattern3 = r'<(file_read|shell|web_search|web_fetch)>([^<]+)</\1>'
            matches3 = re.findall(pattern3, content, re.DOTALL)
            for name, arg_value in matches3:
                arg_key = "path" if name == "file_read" else "command" if name == "shell" else "query" if name == "web_search" else "url"
                tool_calls.append({
                    "id": f"call_{hash(name + arg_value) & 0xFFFFFFFF}",
                    "name": name,
                    "arguments": {arg_key: arg_value.strip()}
                })

        return tool_calls if tool_calls else None

    def _remove_xml_tool_calls(self, content: str) -> str:
        """Remove XML tool calls from content.

        Args:
            content: Original content

        Returns:
            Content with XML tool calls removed
        """
        import re
        content = re.sub(r'<tool>.*?</tool>', '', content, flags=re.DOTALL)
        content = re.sub(r'<function=.*?</function>', '', content, flags=re.DOTALL)
        content = re.sub(r'<(file_read|shell|web_search|web_fetch)>.*?</\1>', '', content, flags=re.DOTALL)
        return content.strip()
