from datetime import date
from typing import List, Optional

from .models import Task
from .repository import TaskRepository


class TodoService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks."""
        # The repository might return all or just active.
        # Our repository implementation splits them.
        return self.repository.get_all()

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks."""
        return self.repository.get_archived()

    def create_task(
        self,
        description: str,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(description=description, priority=priority)
        task.creation_date = date.today()

        if due_date:
            task.attributes["due"] = due_date

        self.repository.save(task)
        return task

    def update_task(
        self,
        task: Task,
        description: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
    ) -> Task:
        """Update an existing task."""
        if description is not None:
            task.description = description

        # Handle priority update (allow clearing it)
        # If priority passed is "", we clear it. If None, we keep it?
        # Let's assume None means "no change", empty string means "remove"
        if priority is not None:
            task.priority = priority if priority else None

        if due_date is not None:
            if due_date:
                task.attributes["due"] = due_date
            elif "due" in task.attributes:
                del task.attributes["due"]

        # Recalculate projects/contexts if description changed
        if description:
            task.__post_init__()

        self.repository.save(task)
        return task

    def complete_task(self, task: Task) -> None:
        """Mark a task as completed."""
        task.complete()
        self.repository.save(task)

    def reopen_task(self, task: Task) -> None:
        """Mark a task as incomplete."""
        task.reopen()
        self.repository.save(task)

    def delete_task(self, task: Task) -> None:
        """Delete a task."""
        self.repository.delete(task)