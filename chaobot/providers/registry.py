"""Provider registry."""

from typing import Any

from chaobot.config.schema import Config, ProviderConfig
from chaobot.providers.base import BaseProvider
from chaobot.providers.spec import ProviderSpec


class ProviderRegistry:
    """Registry for LLM providers."""

    PROVIDERS = {
        "openrouter": ProviderSpec(
            name="openrouter",
            display_name="OpenRouter",
            env_key="OPENROUTER_API_KEY",
            api_base="https://openrouter.ai/api/v1"
        ),
        "anthropic": ProviderSpec(
            name="anthropic",
            display_name="Anthropic",
            env_key="ANTHROPIC_API_KEY",
            api_base="https://api.anthropic.com/v1"
        ),
        "openai": ProviderSpec(
            name="openai",
            display_name="OpenAI",
            env_key="OPENAI_API_KEY",
            api_base="https://api.openai.com/v1"
        ),
        "deepseek": ProviderSpec(
            name="deepseek",
            display_name="DeepSeek",
            env_key="DEEPSEEK_API_KEY",
            api_base="https://api.deepseek.com/v1"
        ),
        "groq": ProviderSpec(
            name="groq",
            display_name="Groq",
            env_key="GROQ_API_KEY",
            api_base="https://api.groq.com/openai/v1"
        ),
        "gemini": ProviderSpec(
            name="gemini",
            display_name="Google Gemini",
            env_key="GEMINI_API_KEY",
            api_base="https://generativelanguage.googleapis.com/v1beta"
        ),
        "custom": ProviderSpec(
            name="custom",
            display_name="Custom",
            supports_tools=True
        ),
    }

    def __init__(self) -> None:
        """Initialize registry."""
        self._providers: dict[str, BaseProvider] = {}

    def get_provider(self, name: str, config: Config) -> BaseProvider:
        """Get a provider instance using LiteLLM.

        Args:
            name: Provider name (deprecated, kept for compatibility)
            config: Application configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_config = self._get_provider_config(name, config) if name else ProviderConfig()
        model = config.agents.defaults.model

        from chaobot.providers.litellm_provider import LiteLLMProvider
        return LiteLLMProvider(config, provider_config, model)

    def get_provider_for_model(self, model: str, config: Config) -> BaseProvider:
        """Get a provider instance for a specific model.

        Args:
            model: Model name in LiteLLM format (e.g., "openai/gpt-4o")
            config: Application configuration

        Returns:
            Provider instance
        """
        provider_name = self._get_provider_name_from_model(model)
        provider_config = self._get_provider_config(provider_name, config)

        from chaobot.providers.litellm_provider import LiteLLMProvider
        return LiteLLMProvider(config, provider_config, model)

    def _get_provider_name_from_model(self, model: str) -> str:
        """Extract provider name from model string.

        Args:
            model: Model name (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")

        Returns:
            Provider name
        """
        if model.startswith("openrouter/"):
            return "openrouter"
        elif model.startswith("anthropic/") or model.startswith("claude"):
            return "anthropic"
        elif model.startswith("openai/"):
            return "openai"
        elif model.startswith("deepseek/"):
            return "deepseek"
        elif model.startswith("groq/"):
            return "groq"
        elif model.startswith("gemini/"):
            return "gemini"
        elif model.startswith("qwen") or model.startswith("qwen3"):
            return "custom"
        else:
            return "custom"

    def _get_provider_config(self, name: str, config: Config) -> ProviderConfig:
        """Get provider configuration.

        Args:
            name: Provider name
            config: Application configuration

        Returns:
            Provider configuration
        """
        providers_config = config.providers

        if name == "openrouter":
            return providers_config.openrouter
        elif name == "anthropic":
            return providers_config.anthropic
        elif name == "openai":
            return providers_config.openai
        elif name == "deepseek":
            return providers_config.deepseek
        elif name == "groq":
            return providers_config.groq
        elif name == "gemini":
            return providers_config.gemini
        elif name == "custom":
            return providers_config.custom
        else:
            return ProviderConfig()

    def get_active_providers(self, config: Config) -> list[str]:
        """Get list of active (configured) providers.

        Args:
            config: Application configuration

        Returns:
            List of active provider names
        """
        active = []

        for name, spec in self.PROVIDERS.items():
            provider_config = self._get_provider_config(name, config)
            if provider_config.enabled and provider_config.api_key:
                active.append(name)

        return active

    def list_providers(self) -> list[dict[str, Any]]:
        """List all available providers.

        Returns:
            List of provider information
        """
        return [
            {
                "name": spec.name,
                "display_name": spec.display_name,
                "env_key": spec.env_key
            }
            for spec in self.PROVIDERS.values()
        ]
