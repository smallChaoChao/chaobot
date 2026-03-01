"""Rate limiter for API calls."""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API calls.

    Supports configurable requests per minute (RPM) limiting.
    """

    def __init__(self, rpm: Optional[int] = None):
        """Initialize rate limiter.

        Args:
            rpm: Requests per minute limit. None means no limit.
        """
        self.rpm = rpm
        self.min_interval = 60.0 / rpm if rpm and rpm > 0 else 0
        self.last_request_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        If rate limit is configured, this will wait if necessary
        to ensure we don't exceed the RPM limit.
        """
        if not self.rpm or self.rpm <= 0:
            return

        async with self._lock:
            now = time.time()

            if self.last_request_time is not None:
                elapsed = now - self.last_request_time
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    await asyncio.sleep(wait_time)

            self.last_request_time = time.time()

    def update_rpm(self, rpm: Optional[int]) -> None:
        """Update the rate limit.

        Args:
            rpm: New requests per minute limit. None means no limit.
        """
        self.rpm = rpm
        self.min_interval = 60.0 / rpm if rpm and rpm > 0 else 0


class ProviderRateLimiter:
    """Rate limiter manager for multiple providers."""

    def __init__(self) -> None:
        """Initialize provider rate limiters."""
        self._limiters: dict[str, RateLimiter] = {}

    def get_limiter(self, provider_name: str, rpm: Optional[int] = None) -> RateLimiter:
        """Get or create a rate limiter for a provider.

        Args:
            provider_name: Name of the provider
            rpm: Requests per minute limit

        Returns:
            RateLimiter instance
        """
        if provider_name not in self._limiters:
            self._limiters[provider_name] = RateLimiter(rpm)
        else:
            # Update RPM if changed
            self._limiters[provider_name].update_rpm(rpm)

        return self._limiters[provider_name]

    async def acquire(self, provider_name: str, rpm: Optional[int] = None) -> None:
        """Acquire permission for a provider.

        Args:
            provider_name: Name of the provider
            rpm: Requests per minute limit (used if limiter doesn't exist)
        """
        limiter = self.get_limiter(provider_name, rpm)
        await limiter.acquire()


# Global rate limiter instance
_global_rate_limiter = ProviderRateLimiter()


def get_rate_limiter() -> ProviderRateLimiter:
    """Get the global rate limiter instance.

    Returns:
        ProviderRateLimiter instance
    """
    return _global_rate_limiter
