from datetime import date

from .exceptions import TaskOperationError, TaskValidationError
from .models import Task
from .repository import TaskRepository, TaskRepositoryError


class TodoService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def _validate_priority(self, priority: str | None) -> None:
        if priority and not (
            len(priority) == 1 and priority.isalpha() and priority.isupper()
        ):
            raise TaskValidationError("Priority must be a single uppercase letter A-Z")

    def get_active_tasks(self) -> list[Task]:
        """Get all active tasks."""
        try:
            # The repository might return all or just active.
            # Our repository implementation splits them.
            return self.repository.get_active_tasks()
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to retrieve active tasks: {e}") from e

    def get_completed_tasks(self) -> list[Task]:
        """Get all completed tasks."""
        try:
            return self.repository.get_completed_tasks()
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to retrieve completed tasks: {e}") from e

    def create_task(
        self,
        description: str,
        priority: str | None = None,
        due_date: date | None = None,
    ) -> Task:
        """Create a new task."""
        if not description or not description.strip():
            raise TaskValidationError("Task description cannot be empty")

        if priority:
            priority = priority.upper()
        self._validate_priority(priority)

        try:
            task = Task(description=description, priority=priority)
            task.creation_date = date.today()

            if due_date:
                task.due_date = due_date

            self.repository.save(task)
            return task
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to create task: {e}") from e

    def update_task(
        self,
        task: Task,
        description: str | None = None,
        priority: str | None = None,
        due_date: date | None = None,
    ) -> Task:
        """Update an existing task."""
        if description is not None:
            if not description.strip():
                raise TaskValidationError("Task description cannot be empty")
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
            task.due_date = due_date

        # Recalculate projects/contexts if description changed
        if description:
            task.refresh_metadata()

        try:
            self.repository.save(task)
            return task
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to update task: {e}") from e

    def complete_task(self, task: Task) -> None:
        """Mark a task as completed."""
        try:
            task.complete()
            self.repository.save(task)
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to complete task: {e}") from e

    def reopen_task(self, task: Task) -> None:
        """Mark a task as incomplete."""
        try:
            task.reopen()
            self.repository.save(task)
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to reopen task: {e}") from e

    def delete_task(self, task: Task) -> None:
        """Delete a task."""
        try:
            self.repository.delete(task)
        except TaskRepositoryError as e:
            raise TaskOperationError(f"Failed to delete task: {e}") from e

    def get_unique_contexts(self) -> list[str]:
        """Get sorted unique @contexts from active tasks."""
        contexts: set[str] = set()
        for task in self.get_active_tasks():
            contexts.update(task.contexts)
        return sorted(contexts)

    def get_unique_projects(self) -> list[str]:
        """Get sorted unique +projects from active tasks."""
        projects: set[str] = set()
        for task in self.get_active_tasks():
            projects.update(task.projects)
        return sorted(projects)
