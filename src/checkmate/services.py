from datetime import date, datetime
from typing import List, Optional

from .models import Task
from .repository import TaskRepository


class TodoService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def _validate_priority(self, priority: Optional[str]) -> None:
        if priority and not (
            len(priority) == 1 and priority.isalpha() and priority.isupper()
        ):
            raise ValueError("Priority must be a single uppercase letter A-Z")

    def _validate_date(self, date_str: Optional[str]) -> None:
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")

    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks."""
        # The repository might return all or just active.
        # Our repository implementation splits them.
        return self.repository.get_active_tasks()

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks."""
        return self.repository.get_completed_tasks()

    def create_task(
        self,
        description: str,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        """Create a new task."""
        if priority:
            priority = priority.upper()
        self._validate_priority(priority)
        self._validate_date(due_date)

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
            if priority:
                priority = priority.upper()
            self._validate_priority(priority)
            task.priority = priority if priority else None

        if due_date is not None:
            self._validate_date(due_date)
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