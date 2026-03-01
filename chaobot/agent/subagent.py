"""Subagent system for background task execution."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class SubagentStatus(Enum):
    """Subagent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubagentTask:
    """A background task executed by subagent."""

    id: str
    description: str
    task_type: str
    params: dict[str, Any]
    status: SubagentStatus = SubagentStatus.PENDING
    result: str = ""
    error: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    parent_session_id: str = ""
    callback_channel: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "task_type": self.task_type,
            "params": self.params,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_session_id": self.parent_session_id,
            "callback_channel": self.callback_channel,
        }


class SubagentManager:
    """Manages subagent tasks and execution."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks: dict[str, SubagentTask] = {}
            cls._instance._running_tasks: dict[str, asyncio.Task] = {}
            cls._instance._callbacks: list[Callable[[SubagentTask], None]] = []
        return cls._instance

    def register_callback(self, callback: Callable[[SubagentTask], None]) -> None:
        """Register a callback for task completion.

        Args:
            callback: Function called when task completes
        """
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[SubagentTask], None]) -> None:
        """Unregister a callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def spawn(
        self,
        description: str,
        task_type: str,
        params: dict[str, Any],
        parent_session_id: str = "",
        callback_channel: str | None = None,
    ) -> SubagentTask:
        """Spawn a new background task.

        Args:
            description: Task description
            task_type: Type of task (e.g., 'code_analysis', 'web_search', 'file_processing')
            params: Task parameters
            parent_session_id: Parent session ID for context
            callback_channel: Channel to notify on completion

        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())[:8]

        task = SubagentTask(
            id=task_id,
            description=description,
            task_type=task_type,
            params=params,
            parent_session_id=parent_session_id,
            callback_channel=callback_channel,
        )

        self._tasks[task_id] = task
        return task

    async def execute_task(
        self,
        task_id: str,
        executor: Callable[[SubagentTask], Any],
    ) -> SubagentTask:
        """Execute a task.

        Args:
            task_id: Task ID
            executor: Async function to execute the task

        Returns:
            Completed task
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.status != SubagentStatus.PENDING:
            raise ValueError(f"Task already started: {task_id}")

        task.status = SubagentStatus.RUNNING
        task.started_at = datetime.now()

        try:
            result = await executor(task)
            task.result = str(result) if result else ""
            task.status = SubagentStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = SubagentStatus.FAILED

        task.completed_at = datetime.now()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(task)
            except Exception:
                pass

        return task

    def start_task(
        self,
        task_id: str,
        executor: Callable[[SubagentTask], Any],
    ) -> asyncio.Task:
        """Start a task in the background.

        Args:
            task_id: Task ID
            executor: Async function to execute the task

        Returns:
            Asyncio task
        """
        async_task = asyncio.create_task(
            self.execute_task(task_id, executor)
        )
        self._running_tasks[task_id] = async_task
        return async_task

    def get_task(self, task_id: str) -> SubagentTask | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: SubagentStatus | None = None,
        parent_session_id: str | None = None,
    ) -> list[SubagentTask]:
        """List tasks with optional filtering.

        Args:
            status: Filter by status
            parent_session_id: Filter by parent session

        Returns:
            List of tasks
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if parent_session_id:
            tasks = [t for t in tasks if t.parent_session_id == parent_session_id]

        return tasks

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status == SubagentStatus.RUNNING and task_id in self._running_tasks:
            async_task = self._running_tasks[task_id]
            async_task.cancel()
            try:
                await async_task
            except asyncio.CancelledError:
                pass

        task.status = SubagentStatus.CANCELLED
        task.completed_at = datetime.now()
        return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False


class SubagentTools:
    """Tools for subagent management."""

    def __init__(self, manager: SubagentManager):
        """Initialize subagent tools.

        Args:
            manager: Subagent manager instance
        """
        self.manager = manager

    async def spawn(
        self,
        description: str,
        task_type: str,
        params: dict[str, Any],
        parent_session_id: str = "",
    ) -> dict:
        """Spawn a background subagent task.

        Args:
            description: Task description
            task_type: Type of task
            params: Task parameters
            parent_session_id: Parent session ID

        Returns:
            Spawn result
        """
        task = self.manager.spawn(
            description=description,
            task_type=task_type,
            params=params,
            parent_session_id=parent_session_id,
        )

        return {
            "success": True,
            "task_id": task.id,
            "description": task.description,
            "status": task.status.value,
            "message": f"Subagent task spawned: {task.id}",
        }

    async def subagent_status(self, task_id: str) -> dict:
        """Get subagent task status.

        Args:
            task_id: Task ID

        Returns:
            Task status
        """
        task = self.manager.get_task(task_id)
        if not task:
            return {
                "success": False,
                "error": f"Task not found: {task_id}",
            }

        return {
            "success": True,
            "task": task.to_dict(),
        }

    async def subagent_list(
        self,
        status: str | None = None,
        parent_session_id: str = "",
    ) -> dict:
        """List subagent tasks.

        Args:
            status: Filter by status
            parent_session_id: Filter by parent session

        Returns:
            List of tasks
        """
        status_enum = SubagentStatus(status) if status else None

        tasks = self.manager.list_tasks(
            status=status_enum,
            parent_session_id=parent_session_id if parent_session_id else None,
        )

        return {
            "success": True,
            "tasks": [t.to_dict() for t in tasks],
        }

    async def subagent_cancel(self, task_id: str) -> dict:
        """Cancel a subagent task.

        Args:
            task_id: Task ID

        Returns:
            Cancellation result
        """
        success = await self.manager.cancel_task(task_id)

        return {
            "success": success,
            "message": "Task cancelled" if success else "Task not found",
        }

    async def subagent_wait(self, task_id: str, timeout: int = 60) -> dict:
        """Wait for a subagent task to complete.

        Args:
            task_id: Task ID
            timeout: Timeout in seconds

        Returns:
            Task result
        """
        task = self.manager.get_task(task_id)
        if not task:
            return {
                "success": False,
                "error": f"Task not found: {task_id}",
            }

        # Wait for completion
        start_time = datetime.now()
        while task.status in (SubagentStatus.PENDING, SubagentStatus.RUNNING):
            await asyncio.sleep(0.5)
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                return {
                    "success": False,
                    "error": f"Timeout waiting for task {task_id}",
                    "task": task.to_dict(),
                }

        return {
            "success": True,
            "task": task.to_dict(),
        }


# Common subagent task executors

async def execute_code_analysis(task: SubagentTask) -> str:
    """Execute code analysis task.

    Args:
        task: Task with params containing 'path' and optional 'patterns'

    Returns:
        Analysis result
    """
    import os
    from pathlib import Path

    path = task.params.get("path", ".")
    patterns = task.params.get("patterns", ["*.py", "*.js", "*.ts"])

    results = []
    base_path = Path(path)

    for pattern in patterns:
        for file_path in base_path.rglob(pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = len(content.splitlines())
                    results.append(f"{file_path}: {lines} lines")
                except Exception as e:
                    results.append(f"{file_path}: Error - {e}")

    return "\n".join(results[:100])  # Limit output


async def execute_web_search(task: SubagentTask) -> str:
    """Execute web search task.

    Args:
        task: Task with params containing 'query' and optional 'max_results'

    Returns:
        Search results
    """
    query = task.params.get("query", "")
    max_results = task.params.get("max_results", 5)

    # This would integrate with the web search tool
    # For now, return a placeholder
    return f"Web search for '{query}' would return {max_results} results"


async def execute_file_processing(task: SubagentTask) -> str:
    """Execute file processing task.

    Args:
        task: Task with params containing 'input_path', 'output_path', 'operation'

    Returns:
        Processing result
    """
    input_path = task.params.get("input_path", "")
    output_path = task.params.get("output_path", "")
    operation = task.params.get("operation", "copy")

    # This would implement various file operations
    return f"File processing: {operation} from {input_path} to {output_path}"


# Registry of task executors
TASK_EXECUTORS: dict[str, Callable[[SubagentTask], Any]] = {
    "code_analysis": execute_code_analysis,
    "web_search": execute_web_search,
    "file_processing": execute_file_processing,
}


def get_executor(task_type: str) -> Callable[[SubagentTask], Any] | None:
    """Get executor for task type.

    Args:
        task_type: Task type

    Returns:
        Executor function or None
    """
    return TASK_EXECUTORS.get(task_type)


def register_executor(
    task_type: str,
    executor: Callable[[SubagentTask], Any]
) -> None:
    """Register a new task executor.

    Args:
        task_type: Task type name
        executor: Executor function
    """
    TASK_EXECUTORS[task_type] = executor
