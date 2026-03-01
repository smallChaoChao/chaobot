"""Tests for task planning system."""

import pytest
from datetime import datetime

from chaobot.agent.planner import (
    TaskStatus,
    TaskStep,
    TaskPlan,
    TaskPlanner,
    PlanTools,
)


class TestTaskStep:
    """Test TaskStep dataclass."""

    def test_task_step_creation(self):
        """Test creating a task step."""
        step = TaskStep(
            id="step_1",
            description="Test step",
            depends_on=["step_0"]
        )
        
        assert step.id == "step_1"
        assert step.description == "Test step"
        assert step.status == TaskStatus.PENDING
        assert step.depends_on == ["step_0"]
        assert step.result == ""
        assert step.error == ""

    def test_task_step_to_dict(self):
        """Test converting step to dictionary."""
        step = TaskStep(
            id="step_1",
            description="Test step",
            status=TaskStatus.COMPLETED,
            result="Done"
        )
        
        data = step.to_dict()
        assert data["id"] == "step_1"
        assert data["description"] == "Test step"
        assert data["status"] == "completed"
        assert data["result"] == "Done"


class TestTaskPlan:
    """Test TaskPlan dataclass."""

    def test_task_plan_creation(self):
        """Test creating a task plan."""
        steps = [
            TaskStep(id="step_1", description="Step 1"),
            TaskStep(id="step_2", description="Step 2"),
        ]
        
        plan = TaskPlan(
            id="plan_1",
            title="Test Plan",
            description="A test plan",
            steps=steps
        )
        
        assert plan.id == "plan_1"
        assert plan.title == "Test Plan"
        assert plan.description == "A test plan"
        assert len(plan.steps) == 2
        assert plan.status == TaskStatus.PENDING

    def test_get_pending_steps_no_dependencies(self):
        """Test getting pending steps with no dependencies."""
        steps = [
            TaskStep(id="step_1", description="Step 1"),
            TaskStep(id="step_2", description="Step 2"),
        ]
        
        plan = TaskPlan(
            id="plan_1",
            title="Test Plan",
            description="Test",
            steps=steps
        )
        
        pending = plan.get_pending_steps()
        assert len(pending) == 2
        assert pending[0].id == "step_1"
        assert pending[1].id == "step_2"

    def test_get_pending_steps_with_dependencies(self):
        """Test getting pending steps with dependencies."""
        steps = [
            TaskStep(id="step_1", description="Step 1"),
            TaskStep(
                id="step_2",
                description="Step 2",
                depends_on=["step_1"]
            ),
        ]
        
        plan = TaskPlan(
            id="plan_1",
            title="Test Plan",
            description="Test",
            steps=steps
        )
        
        # Initially only step_1 is pending (step_2 depends on it)
        pending = plan.get_pending_steps()
        assert len(pending) == 1
        assert pending[0].id == "step_1"
        
        # Mark step_1 as completed
        plan.steps[0].status = TaskStatus.COMPLETED
        
        # Now step_2 should be pending
        pending = plan.get_pending_steps()
        assert len(pending) == 1
        assert pending[0].id == "step_2"

    def test_update_status_completed(self):
        """Test updating plan status to completed."""
        steps = [
            TaskStep(id="step_1", description="Step 1", status=TaskStatus.COMPLETED),
            TaskStep(id="step_2", description="Step 2", status=TaskStatus.COMPLETED),
        ]
        
        plan = TaskPlan(
            id="plan_1",
            title="Test Plan",
            description="Test",
            steps=steps
        )
        
        plan.update_status()
        assert plan.status == TaskStatus.COMPLETED
        assert plan.completed_at is not None

    def test_update_status_failed(self):
        """Test updating plan status to failed."""
        steps = [
            TaskStep(id="step_1", description="Step 1", status=TaskStatus.COMPLETED),
            TaskStep(id="step_2", description="Step 2", status=TaskStatus.FAILED),
        ]
        
        plan = TaskPlan(
            id="plan_1",
            title="Test Plan",
            description="Test",
            steps=steps
        )
        
        plan.update_status()
        assert plan.status == TaskStatus.FAILED


class TestTaskPlanner:
    """Test TaskPlanner."""

    @pytest.fixture(autouse=True)
    def reset_planner(self):
        """Reset planner singleton before each test."""
        # Clear the singleton instance
        TaskPlanner._instance = None
        yield
        # Clean up after test
        TaskPlanner._instance = None

    def test_create_plan(self):
        """Test creating a plan."""
        planner = TaskPlanner()
        
        steps = [
            {"description": "Step 1"},
            {"description": "Step 2"},
        ]
        
        plan = planner.create_plan(
            title="Test Plan",
            description="A test plan",
            steps=steps
        )
        
        assert plan.title == "Test Plan"
        assert plan.description == "A test plan"
        assert len(plan.steps) == 2
        assert plan.steps[0].id == "step_0"
        assert plan.steps[1].id == "step_1"

    def test_create_plan_with_dependencies(self):
        """Test creating a plan with step dependencies."""
        planner = TaskPlanner()
        
        steps = [
            {"description": "Step 1", "id": "setup"},
            {"description": "Step 2", "id": "execute", "depends_on": ["setup"]},
        ]
        
        plan = planner.create_plan(
            title="Test Plan",
            description="Test",
            steps=steps
        )
        
        assert plan.steps[0].id == "setup"
        assert plan.steps[1].id == "execute"
        assert plan.steps[1].depends_on == ["setup"]

    def test_get_plan(self):
        """Test retrieving a plan by ID."""
        planner = TaskPlanner()
        
        plan = planner.create_plan(
            title="Test",
            description="Test",
            steps=[{"description": "Step 1"}]
        )
        
        retrieved = planner.get_plan(plan.id)
        assert retrieved is not None
        assert retrieved.id == plan.id

    def test_get_nonexistent_plan(self):
        """Test retrieving a non-existent plan."""
        planner = TaskPlanner()
        
        retrieved = planner.get_plan("nonexistent")
        assert retrieved is None

    def test_list_plans(self):
        """Test listing all plans."""
        planner = TaskPlanner()
        
        planner.create_plan(
            title="Plan 1",
            description="Test",
            steps=[{"description": "Step"}]
        )
        planner.create_plan(
            title="Plan 2",
            description="Test",
            steps=[{"description": "Step"}]
        )
        
        plans = planner.list_plans()
        assert len(plans) == 2

    @pytest.mark.asyncio
    async def test_execute_plan(self):
        """Test executing a plan."""
        planner = TaskPlanner()
        
        plan = planner.create_plan(
            title="Test Plan",
            description="Test",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        async def mock_executor(step):
            return f"Completed {step.description}"
        
        completed_plan = await planner.execute_plan(
            plan.id,
            execute_step=mock_executor
        )
        
        assert completed_plan.status == TaskStatus.COMPLETED
        assert completed_plan.steps[0].status == TaskStatus.COMPLETED
        assert completed_plan.steps[1].status == TaskStatus.COMPLETED
        assert completed_plan.steps[0].result == "Completed Step 1"

    @pytest.mark.asyncio
    async def test_execute_plan_with_failure(self):
        """Test executing a plan where a step fails."""
        planner = TaskPlanner()
        
        plan = planner.create_plan(
            title="Test Plan",
            description="Test",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        async def mock_executor(step):
            # Fail the first step (step_0)
            if step.id == "step_0":
                raise Exception("Step failed")
            return "Success"
        
        completed_plan = await planner.execute_plan(
            plan.id,
            execute_step=mock_executor
        )
        
        assert completed_plan.status == TaskStatus.FAILED
        assert completed_plan.steps[0].status == TaskStatus.FAILED
        assert "Step failed" in completed_plan.steps[0].error

    def test_cancel_plan(self):
        """Test cancelling a plan."""
        planner = TaskPlanner()
        
        plan = planner.create_plan(
            title="Test Plan",
            description="Test",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        success = planner.cancel_plan(plan.id)
        assert success is True
        assert plan.steps[0].status == TaskStatus.CANCELLED
        assert plan.steps[1].status == TaskStatus.CANCELLED


class TestPlanTools:
    """Test PlanTools."""

    @pytest.mark.asyncio
    async def test_plan_create(self):
        """Test plan_create tool."""
        planner = TaskPlanner()
        plan_tools = PlanTools(planner)
        
        result = await plan_tools.plan_create(
            title="Test Plan",
            description="A test plan",
            steps=["Step 1", "Step 2"]
        )
        
        assert result["success"] is True
        assert "plan_id" in result
        assert result["title"] == "Test Plan"
        assert result["step_count"] == 2

    @pytest.mark.asyncio
    async def test_plan_list(self):
        """Test plan_list tool."""
        planner = TaskPlanner()
        plan_tools = PlanTools(planner)
        
        # Create a plan first
        await plan_tools.plan_create(
            title="Test Plan",
            description="Test",
            steps=["Step 1"]
        )
        
        result = await plan_tools.plan_list()
        
        assert result["success"] is True
        assert len(result["plans"]) == 1
        assert result["plans"][0]["title"] == "Test Plan"

    @pytest.mark.asyncio
    async def test_plan_status(self):
        """Test plan_status tool."""
        planner = TaskPlanner()
        plan_tools = PlanTools(planner)
        
        # Create a plan
        create_result = await plan_tools.plan_create(
            title="Test Plan",
            description="Test",
            steps=["Step 1"]
        )
        
        plan_id = create_result["plan_id"]
        
        # Get status
        result = await plan_tools.plan_status(plan_id)
        
        assert result["success"] is True
        assert result["plan"]["title"] == "Test Plan"

    @pytest.mark.asyncio
    async def test_plan_status_not_found(self):
        """Test plan_status with non-existent plan."""
        planner = TaskPlanner()
        plan_tools = PlanTools(planner)
        
        result = await plan_tools.plan_status("nonexistent")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_plan_cancel(self):
        """Test plan_cancel tool."""
        planner = TaskPlanner()
        plan_tools = PlanTools(planner)
        
        # Create a plan
        create_result = await plan_tools.plan_create(
            title="Test Plan",
            description="Test",
            steps=["Step 1"]
        )
        
        plan_id = create_result["plan_id"]
        
        # Cancel it
        result = await plan_tools.plan_cancel(plan_id)
        
        assert result["success"] is True
