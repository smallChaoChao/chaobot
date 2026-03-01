"""Task planning system for complex multi-step tasks."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """A single step in a task plan."""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    error: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    depends_on: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "depends_on": self.depends_on,
            "tool_calls": self.tool_calls,
        }


@dataclass
class TaskPlan:
    """A task plan containing multiple steps."""

    id: str
    title: str
    description: str
    steps: list[TaskStep]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    def get_pending_steps(self) -> list[TaskStep]:
        """Get steps that are ready to execute (pending and dependencies met)."""
        completed_ids = {
            step.id for step in self.steps
            if step.status == TaskStatus.COMPLETED
        }

        return [
            step for step in self.steps
            if step.status == TaskStatus.PENDING
            and all(dep in completed_ids for dep in step.depends_on)
        ]

    def get_step(self, step_id: str) -> TaskStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def update_status(self) -> None:
        """Update overall plan status based on steps."""
        if all(step.status == TaskStatus.COMPLETED for step in self.steps):
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now()
        elif any(step.status == TaskStatus.FAILED for step in self.steps):
            self.status = TaskStatus.FAILED
        elif any(step.status == TaskStatus.IN_PROGRESS for step in self.steps):
            self.status = TaskStatus.IN_PROGRESS


class TaskPlanner:
    """Plans and executes complex multi-step tasks."""

    def __init__(self):
        """Initialize task planner."""
        self._plans: dict[str, TaskPlan] = {}

    def create_plan(
        self,
        title: str,
        description: str,
        steps: list[dict],
        metadata: dict[str, Any] | None = None
    ) -> TaskPlan:
        """Create a new task plan.

        Args:
            title: Plan title
            description: Plan description
            steps: List of step definitions with 'description' and optional 'depends_on'
            metadata: Additional metadata

        Returns:
            Created task plan
        """
        plan_id = str(uuid.uuid4())[:8]

        task_steps = []
        for i, step_def in enumerate(steps):
            step = TaskStep(
                id=step_def.get("id", f"step_{i}"),
                description=step_def["description"],
                depends_on=step_def.get("depends_on", []),
            )
            task_steps.append(step)

        plan = TaskPlan(
            id=plan_id,
            title=title,
            description=description,
            steps=task_steps,
            metadata=metadata or {},
        )

        self._plans[plan_id] = plan
        return plan

    def get_plan(self, plan_id: str) -> TaskPlan | None:
        """Get plan by ID."""
        return self._plans.get(plan_id)

    def list_plans(self) -> list[TaskPlan]:
        """List all plans."""
        return list(self._plans.values())

    async def execute_plan(
        self,
        plan_id: str,
        execute_step: Callable[[TaskStep], Any],
        on_progress: Callable[[TaskStep, TaskPlan], None] | None = None,
    ) -> TaskPlan:
        """Execute a task plan.

        Args:
            plan_id: Plan ID
            execute_step: Async function to execute a step
            on_progress: Optional callback for progress updates

        Returns:
            Completed plan
        """
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        plan.status = TaskStatus.IN_PROGRESS

        while True:
            pending = plan.get_pending_steps()
            if not pending:
                break

            # Execute steps that are ready
            for step in pending:
                step.status = TaskStatus.IN_PROGRESS
                step.started_at = datetime.now()

                if on_progress:
                    on_progress(step, plan)

                try:
                    result = await execute_step(step)
                    step.result = str(result) if result else ""
                    step.status = TaskStatus.COMPLETED
                except Exception as e:
                    step.error = str(e)
                    step.status = TaskStatus.FAILED

                step.completed_at = datetime.now()

                if on_progress:
                    on_progress(step, plan)

            plan.update_status()

            if plan.status == TaskStatus.FAILED:
                break

        return plan

    def cancel_plan(self, plan_id: str) -> bool:
        """Cancel a plan.

        Args:
            plan_id: Plan ID

        Returns:
            True if cancelled
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.status == TaskStatus.PENDING:
                step.status = TaskStatus.CANCELLED

        plan.update_status()
        return True

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan.

        Args:
            plan_id: Plan ID

        Returns:
            True if deleted
        """
        if plan_id in self._plans:
            del self._plans[plan_id]
            return True
        return False


class PlanTools:
    """Tools for plan management."""

    def __init__(self, planner: TaskPlanner):
        """Initialize plan tools.

        Args:
            planner: Task planner instance
        """
        self.planner = planner

    async def plan_create(
        self,
        title: str,
        description: str,
        steps: list[str],
    ) -> dict:
        """Create a new task plan.

        Args:
            title: Plan title
            description: Plan description
            steps: List of step descriptions

        Returns:
            Plan creation result
        """
        step_defs = [
            {"description": step, "id": f"step_{i}"}
            for i, step in enumerate(steps)
        ]

        plan = self.planner.create_plan(
            title=title,
            description=description,
            steps=step_defs,
        )

        return {
            "success": True,
            "plan_id": plan.id,
            "title": plan.title,
            "step_count": len(plan.steps),
        }

    async def plan_add_step(
        self,
        plan_id: str,
        description: str,
        depends_on: list[str] | None = None,
    ) -> dict:
        """Add a step to an existing plan.

        Args:
            plan_id: Plan ID
            description: Step description
            depends_on: IDs of steps this depends on

        Returns:
            Step addition result
        """
        plan = self.planner.get_plan(plan_id)
        if not plan:
            return {
                "success": False,
                "error": f"Plan not found: {plan_id}",
            }

        step_id = f"step_{len(plan.steps)}"
        step = TaskStep(
            id=step_id,
            description=description,
            depends_on=depends_on or [],
        )
        plan.steps.append(step)

        return {
            "success": True,
            "step_id": step_id,
            "plan_id": plan_id,
        }

    async def plan_status(self, plan_id: str) -> dict:
        """Get plan status.

        Args:
            plan_id: Plan ID

        Returns:
            Plan status information
        """
        plan = self.planner.get_plan(plan_id)
        if not plan:
            return {
                "success": False,
                "error": f"Plan not found: {plan_id}",
            }

        return {
            "success": True,
            "plan": plan.to_dict(),
        }

    async def plan_list(self) -> dict:
        """List all plans.

        Returns:
            List of plans
        """
        plans = self.planner.list_plans()

        return {
            "success": True,
            "plans": [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status.value,
                    "step_count": len(p.steps),
                    "completed_steps": sum(
                        1 for s in p.steps if s.status == TaskStatus.COMPLETED
                    ),
                }
                for p in plans
            ],
        }

    async def plan_cancel(self, plan_id: str) -> dict:
        """Cancel a plan.

        Args:
            plan_id: Plan ID

        Returns:
            Cancellation result
        """
        success = self.planner.cancel_plan(plan_id)

        return {
            "success": success,
            "message": "Plan cancelled" if success else "Plan not found",
        }
