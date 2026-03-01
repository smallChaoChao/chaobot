"""Tests for subagent system."""

import pytest
from datetime import datetime

from chaobot.agent.subagent import (
    SubagentStatus,
    SubagentTask,
    SubagentManager,
    SubagentTools,
    get_executor,
    register_executor,
    TASK_EXECUTORS,
)


class TestSubagentTask:
    """Test SubagentTask dataclass."""

    def test_task_creation(self):
        """Test creating a subagent task."""
        task = SubagentTask(
            id="task_1",
            description="Test task",
            task_type="code_analysis",
            params={"path": ".", "patterns": ["*.py"]},
            parent_session_id="session_123"
        )
        
        assert task.id == "task_1"
        assert task.description == "Test task"
        assert task.task_type == "code_analysis"
        assert task.params == {"path": ".", "patterns": ["*.py"]}
        assert task.status == SubagentStatus.PENDING
        assert task.parent_session_id == "session_123"

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = SubagentTask(
            id="task_1",
            description="Test task",
            task_type="test",
            params={},
            status=SubagentStatus.COMPLETED,
            result="Done"
        )
        
        data = task.to_dict()
        assert data["id"] == "task_1"
        assert data["description"] == "Test task"
        assert data["status"] == "completed"
        assert data["result"] == "Done"


class TestSubagentManager:
    """Test SubagentManager singleton."""

    def test_singleton_pattern(self):
        """Test that SubagentManager is a singleton."""
        manager1 = SubagentManager()
        manager2 = SubagentManager()
        assert manager1 is manager2

    def test_spawn_task(self):
        """Test spawning a new task."""
        manager = SubagentManager()
        # Clear any existing tasks
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="code_analysis",
            params={"path": "."},
            parent_session_id="session_123"
        )
        
        assert task.id is not None
        assert task.description == "Test task"
        assert task.task_type == "code_analysis"
        assert task.parent_session_id == "session_123"
        assert task.status == SubagentStatus.PENDING

    def test_get_task(self):
        """Test retrieving a task by ID."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        retrieved = manager.get_task(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id

    def test_get_nonexistent_task(self):
        """Test retrieving a non-existent task."""
        manager = SubagentManager()
        
        retrieved = manager.get_task("nonexistent")
        assert retrieved is None

    def test_list_tasks(self):
        """Test listing all tasks."""
        manager = SubagentManager()
        manager._tasks = {}
        
        manager.spawn(description="Task 1", task_type="test", params={})
        manager.spawn(description="Task 2", task_type="test", params={})
        
        tasks = manager.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_with_filter(self):
        """Test listing tasks with status filter."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task1 = manager.spawn(description="Task 1", task_type="test", params={})
        task2 = manager.spawn(description="Task 2", task_type="test", params={})
        
        # Mark one as completed
        task1.status = SubagentStatus.COMPLETED
        
        pending_tasks = manager.list_tasks(status=SubagentStatus.PENDING)
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == task2.id

    def test_list_tasks_by_parent_session(self):
        """Test listing tasks by parent session."""
        manager = SubagentManager()
        manager._tasks = {}
        
        manager.spawn(
            description="Task 1",
            task_type="test",
            params={},
            parent_session_id="session_1"
        )
        manager.spawn(
            description="Task 2",
            task_type="test",
            params={},
            parent_session_id="session_2"
        )
        
        session_tasks = manager.list_tasks(parent_session_id="session_1")
        assert len(session_tasks) == 1
        assert session_tasks[0].description == "Task 1"

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test executing a task."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        async def mock_executor(task):
            return "Task completed successfully"
        
        completed_task = await manager.execute_task(task.id, mock_executor)
        
        assert completed_task.status == SubagentStatus.COMPLETED
        assert completed_task.result == "Task completed successfully"

    @pytest.mark.asyncio
    async def test_execute_task_with_failure(self):
        """Test executing a task that fails."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        async def mock_executor(task):
            raise Exception("Task failed")
        
        completed_task = await manager.execute_task(task.id, mock_executor)
        
        assert completed_task.status == SubagentStatus.FAILED
        assert "Task failed" in completed_task.error

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test cancelling a task."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        success = await manager.cancel_task(task.id)
        assert success is True
        assert task.status == SubagentStatus.CANCELLED

    def test_delete_task(self):
        """Test deleting a task."""
        manager = SubagentManager()
        manager._tasks = {}
        
        task = manager.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        success = manager.delete_task(task.id)
        assert success is True
        assert manager.get_task(task.id) is None


class TestSubagentTools:
    """Test SubagentTools."""

    @pytest.mark.asyncio
    async def test_spawn(self):
        """Test spawn tool."""
        manager = SubagentManager()
        manager._tasks = {}
        subagent_tools = SubagentTools(manager)
        
        result = await subagent_tools.spawn(
            description="Test task",
            task_type="code_analysis",
            params={"path": "."},
            parent_session_id="session_123"
        )
        
        assert result["success"] is True
        assert "task_id" in result
        assert result["description"] == "Test task"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_subagent_status(self):
        """Test subagent_status tool."""
        manager = SubagentManager()
        manager._tasks = {}
        subagent_tools = SubagentTools(manager)
        
        # Create a task
        spawn_result = await subagent_tools.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        task_id = spawn_result["task_id"]
        
        # Get status
        result = await subagent_tools.subagent_status(task_id)
        
        assert result["success"] is True
        assert result["task"]["description"] == "Test task"

    @pytest.mark.asyncio
    async def test_subagent_status_not_found(self):
        """Test subagent_status with non-existent task."""
        manager = SubagentManager()
        subagent_tools = SubagentTools(manager)
        
        result = await subagent_tools.subagent_status("nonexistent")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_subagent_list(self):
        """Test subagent_list tool."""
        manager = SubagentManager()
        manager._tasks = {}
        subagent_tools = SubagentTools(manager)
        
        # Create tasks
        await subagent_tools.spawn(
            description="Task 1",
            task_type="test",
            params={},
            parent_session_id="session_1"
        )
        await subagent_tools.spawn(
            description="Task 2",
            task_type="test",
            params={},
            parent_session_id="session_1"
        )
        
        result = await subagent_tools.subagent_list(parent_session_id="session_1")
        
        assert result["success"] is True
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_subagent_cancel(self):
        """Test subagent_cancel tool."""
        manager = SubagentManager()
        manager._tasks = {}
        subagent_tools = SubagentTools(manager)
        
        # Create a task
        spawn_result = await subagent_tools.spawn(
            description="Test task",
            task_type="test",
            params={}
        )
        
        task_id = spawn_result["task_id"]
        
        # Cancel it
        result = await subagent_tools.subagent_cancel(task_id)
        
        assert result["success"] is True


class TestExecutors:
    """Test task executors."""

    def test_get_executor_existing(self):
        """Test getting an existing executor."""
        # Register a test executor
        async def test_executor(task):
            return "test result"
        
        register_executor("test_type", test_executor)
        
        executor = get_executor("test_type")
        assert executor is not None
        assert executor == test_executor

    def test_get_executor_nonexistent(self):
        """Test getting a non-existent executor."""
        executor = get_executor("nonexistent_type")
        assert executor is None

    def test_register_executor(self):
        """Test registering a new executor."""
        async def new_executor(task):
            return "new result"
        
        register_executor("new_type", new_executor)
        
        assert "new_type" in TASK_EXECUTORS
        assert TASK_EXECUTORS["new_type"] == new_executor
