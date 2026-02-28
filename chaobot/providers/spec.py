"""Provider specification."""

from dataclasses import dataclass


@dataclass
class ProviderSpec:
    """Provider specification."""

    name: str
    display_name: str
    env_key: str | None = None
    api_base: str | None = None
    supports_tools: bool = True
