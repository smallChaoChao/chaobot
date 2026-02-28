"""Cron job manager."""

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import schedule

from chaobot.config.manager import ConfigManager


@dataclass
class CronTask:
    """Scheduled task."""

    id: str
    name: str
    message: str
    schedule: str
    task_type: str  # "cron" or "interval"


class CronManager:
    """Manager for scheduled tasks."""

    def __init__(self) -> None:
        """Initialize cron manager."""
        config = ConfigManager().load()
        self.tasks_file = config.workspace_path / "cron_tasks.json"
        self.tasks: list[CronTask] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from file."""
        if self.tasks_file.exists():
            with open(self.tasks_file) as f:
                data = json.load(f)
                self.tasks = [CronTask(**task) for task in data]

    def _save_tasks(self) -> None:
        """Save tasks to file."""
        with open(self.tasks_file, "w") as f:
            json.dump([asdict(task) for task in self.tasks], f, indent=2)

    def add_cron(self, name: str, message: str, cron_expr: str) -> CronTask:
        """Add a cron task.

        Args:
            name: Task name
            message: Message to send
            cron_expr: Cron expression

        Returns:
            Created task
        """
        task = CronTask(
            id=str(uuid.uuid4())[:8],
            name=name,
            message=message,
            schedule=cron_expr,
            task_type="cron"
        )
        self.tasks.append(task)
        self._save_tasks()
        return task

    def add_interval(self, name: str, message: str, seconds: int) -> CronTask:
        """Add an interval task.

        Args:
            name: Task name
            message: Message to send
            seconds: Interval in seconds

        Returns:
            Created task
        """
        task = CronTask(
            id=str(uuid.uuid4())[:8],
            name=name,
            message=message,
            schedule=f"every {seconds}s",
            task_type="interval"
        )
        self.tasks.append(task)
        self._save_tasks()
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a task.

        Args:
            task_id: Task ID

        Returns:
            True if removed
        """
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                self._save_tasks()
                return True
        return False

    def list_tasks(self) -> list[CronTask]:
        """List all tasks.

        Returns:
            List of tasks
        """
        return self.tasks.copy()

    def run_pending(self) -> None:
        """Run pending tasks."""
        schedule.run_pending()
