"""Configuration schema using Pydantic."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    model_config = {"populate_by_name": True}

    enabled: bool = Field(default=True, alias="enabled")
    api_key: str | None = Field(default=None, alias="api_key")
    api_base: str | None = Field(default=None, alias="api_base")
    timeout: int = Field(default=120, alias="timeout")
    max_retries: int = Field(default=5, alias="max_retries")
    rate_limit_rpm: int | None = Field(default=None, alias="rate_limit_rpm")


class ProvidersConfig(BaseModel):
    """All provider configurations."""

    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    custom: ProviderConfig = Field(default_factory=ProviderConfig)


class AgentDefaultsConfig(BaseModel):
    """Default agent settings."""

    model: str = "anthropic/claude-3-5-sonnet-20241022"
    provider: str = "openrouter"
    temperature: float = 0.7
    max_tokens: int | None = None
    system_prompt: str | None = None


class AgentConfig(BaseModel):
    """Agent configuration."""

    defaults: AgentDefaultsConfig = Field(default_factory=AgentDefaultsConfig)
    max_iterations: int = 50
    context_window: int = 100000


class TelegramChannelConfig(BaseModel):
    """Telegram channel configuration."""

    enabled: bool = False
    token: str | None = None
    allow_from: list[str] = Field(default_factory=list)


class DiscordChannelConfig(BaseModel):
    """Discord channel configuration."""

    enabled: bool = False
    token: str | None = None
    allow_from: list[str] = Field(default_factory=list)


class FeishuChannelConfig(BaseModel):
    """Feishu/Lark channel configuration using WebSocket long connection."""

    enabled: bool = False
    app_id: str | None = None
    app_secret: str | None = None
    webhook_url: str | None = None  # Deprecated, kept for compatibility
    bot_name: str = "chaobot"
    encrypt_key: str | None = None
    verification_token: str | None = None
    allow_from: list[str] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    """All channel configurations."""

    telegram: TelegramChannelConfig = Field(default_factory=TelegramChannelConfig)
    discord: DiscordChannelConfig = Field(default_factory=DiscordChannelConfig)
    feishu: FeishuChannelConfig = Field(default_factory=FeishuChannelConfig)


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    tool_timeout: int = 30


class ToolsConfig(BaseModel):
    """Tools configuration."""

    model_config = {"populate_by_name": True}

    restrict_to_workspace: bool = Field(default=False, alias="restrict_to_workspace")
    exec_path_append: str = Field(default="", alias="exec_path_append")
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict, alias="mcp_servers")
    brave_api_key: str | None = Field(default=None, alias="brave_api_key")


class SecurityConfig(BaseModel):
    """Security configuration."""

    confirm_destructive_actions: bool = True
    allowed_commands: list[str] = Field(default_factory=list)
    blocked_commands: list[str] = Field(default_factory=list)


class Config(BaseSettings):
    """Main configuration."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    providers: ProvidersConfig = Field(default_factory=ProvidersConfig, alias="providers")
    agents: AgentConfig = Field(default_factory=AgentConfig, alias="agents")
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig, alias="channels")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, alias="tools")
    security: SecurityConfig = Field(default_factory=SecurityConfig, alias="security")

    # Paths (set by ConfigManager)
    config_path: Path = Path.home() / ".chaobot" / "config.json"
    workspace_path: Path = Path.home() / ".chaobot" / "workspace"

    @field_validator("providers", "agents", "channels", "tools", "security", mode="before")
    @classmethod
    def set_defaults(cls, v: Any) -> Any:
        """Ensure nested models have defaults."""
        if v is None:
            return {}
        return v
