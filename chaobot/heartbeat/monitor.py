"""Heartbeat monitor for periodic tasks."""

import asyncio
from pathlib import Path
from typing import Any

from chaobot.config.schema import Config


class HeartbeatMonitor:
    """Monitors HEARTBEAT.md for periodic tasks."""

    def __init__(self, config: Config) -> None:
        """Initialize heartbeat monitor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.heartbeat_file = config.workspace_path / "HEARTBEAT.md"
        self.interval = 1800  # 30 minutes

    async def start(self) -> None:
        """Start monitoring."""
        while True:
            await self._check_heartbeat()
            await asyncio.sleep(self.interval)

    async def _check_heartbeat(self) -> None:
        """Check heartbeat file for tasks."""
        if not self.heartbeat_file.exists():
            return

        content = self.heartbeat_file.read_text()

        # Parse tasks from markdown
        tasks = self._parse_tasks(content)

        for task in tasks:
            if not task.get("done", False):
                # Execute task
                await self._execute_task(task)

    def _parse_tasks(self, content: str) -> list[dict[str, Any]]:
        """Parse tasks from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of tasks
        """
        tasks = []

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
                done = line.startswith("- [x]")
                task_text = line[5:].strip()
                tasks.append({
                    "text": task_text,
                    "done": done
                })

        return tasks

    async def _execute_task(self, task: dict[str, Any]) -> None:
        """Execute a task.

        Args:
            task: Task dictionary
        """
        # TODO: Implement task execution
        # This would involve calling the agent with the task
        pass
