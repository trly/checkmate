import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from pytodotxt import Task as PytodoTask
from pytodotxt import TodoTxt

from .models import Task


class TaskRepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class TaskRepository(ABC):
    @abstractmethod
    def get_active_tasks(self) -> list[Task]:
        """Get all active tasks."""
        pass

    @abstractmethod
    def get_completed_tasks(self) -> list[Task]:
        """Get all completed tasks."""
        pass

    @abstractmethod
    def save(self, task: Task) -> None:
        """Save a task (create or update)."""
        pass

    @abstractmethod
    def delete(self, task: Task) -> None:
        """Delete a task."""
        pass


class _TaskWithMeta(Task):
    """Internal wrapper to track persistence details."""

    __slots__ = ("_original_text",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_text: str | None = None


class FileTaskRepository(TaskRepository):
    def __init__(self, todo_file: str, done_file: str):
        self.todo_file = Path(todo_file).resolve()
        self.done_file = Path(done_file).resolve()

        if self.todo_file == self.done_file:
            raise ValueError("todo_file and done_file must be distinct")

        try:
            self._ensure_files_exist()
        except Exception as e:
            raise ValueError(f"Repository files not accessible: {e}") from e

    def _ensure_files_exist(self):
        self._create_file_if_missing(self.todo_file)
        self._create_file_if_missing(self.done_file)

    def _create_file_if_missing(self, path: Path):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def _to_domain(self, pytodo_task: PytodoTask) -> Task:
        # PytodoTask attributes are lists, we need to handle that
        attrs = {}
        pytodo_attrs = getattr(pytodo_task, "attributes", None)
        if pytodo_attrs is not None:
            attrs = pytodo_attrs.copy()

        description = pytodo_task.description or ""

        # Strip attributes from description to prevent duplication
        if attrs:
            for key, values in attrs.items():
                # values is typically a list in pytodotxt
                if isinstance(values, list):
                    for val in values:
                        description = description.replace(f"{key}:{val}", "")
                else:
                    description = description.replace(f"{key}:{values}", "")

            # Clean up extra whitespace
            description = " ".join(description.split())

        task = _TaskWithMeta(
            description=description,
            is_completed=pytodo_task.is_completed or False,
            priority=pytodo_task.priority,
            creation_date=pytodo_task.creation_date,
            completion_date=pytodo_task.completion_date,
            projects=pytodo_task.projects if hasattr(pytodo_task, "projects") else [],
            contexts=pytodo_task.contexts if hasattr(pytodo_task, "contexts") else [],
            attributes=attrs,
        )
        task._original_text = str(pytodo_task)
        return task

    def _to_pytodo(self, task: Task) -> PytodoTask:
        # Construct string representation to create PytodoTask
        t = PytodoTask(task.description)
        t.is_completed = task.is_completed
        t.priority = task.priority
        t.creation_date = task.creation_date
        t.completion_date = task.completion_date

        # Attributes in pytodotxt are tricky, usually parsed from string.
        for k, v in task.attributes.items():
            if isinstance(v, list):
                for item in v:
                    t.add_attribute(k, item)
            else:
                t.add_attribute(k, str(v))

        return t

    def get_active_tasks(self) -> list[Task]:
        """Get all active tasks from todo.txt."""
        try:
            todotxt = TodoTxt(str(self.todo_file))
            todotxt.parse()
            return [self._to_domain(t) for t in todotxt.tasks]
        except Exception as e:
            raise TaskRepositoryError(f"Failed to load active tasks: {e}") from e

    def get_completed_tasks(self) -> list[Task]:
        """Get all completed tasks from done.txt."""
        try:
            donetxt = TodoTxt(str(self.done_file))
            donetxt.parse()
            return [self._to_domain(t) for t in donetxt.tasks]
        except Exception as e:
            raise TaskRepositoryError(f"Failed to load completed tasks: {e}") from e

    def save(self, task: Task) -> None:
        """Save a task (create or update)."""
        try:
            # Generate stable ID if missing
            if "cmid" not in task.attributes:
                task.attributes["cmid"] = uuid.uuid4().hex[:8]

            pytodo_task = self._to_pytodo(task)
            new_text = str(pytodo_task)

            # If we have an ID, try to find and remove by ID first
            removed_by_id = False
            if task.id:
                removed_by_id = self._remove_by_id(self.todo_file, task.id)
                if not removed_by_id:
                    removed_by_id = self._remove_by_id(self.done_file, task.id)

            # If not removed by ID (e.g. legacy task), fallback to original text
            original_text = getattr(task, "_original_text", None)
            if not removed_by_id and original_text:
                # Check if the text actually changed to avoid unnecessary IO
                if original_text == new_text:
                    # However, we might be moving files (completing/uncompleting)
                    # So we still need to check logic below
                    pass

                # Try to remove from both files to be safe (in case it moved)
                self._remove_from_file(self.todo_file, original_text)
                self._remove_from_file(self.done_file, original_text)

            # Determine target file based on current state
            target_file = self.done_file if task.is_completed else self.todo_file

            # Add to target file
            todotxt = TodoTxt(str(target_file))
            todotxt.parse()
            todotxt.tasks.append(pytodo_task)
            todotxt.save()

            # Update original text for future updates
            if isinstance(task, _TaskWithMeta):
                task._original_text = new_text
        except Exception as e:
            raise TaskRepositoryError(f"Failed to save task: {e}") from e
        # If it's a plain Task, we can't attach _original_text unless wrapped.
        # But if we are saving a new task, it might become a legacy update later
        # if we don't track it? But we HAVE generated an ID!
        # So future updates will use ID.

    def delete(self, task: Task) -> None:
        """Delete a task."""
        try:
            # Try to delete by ID first if available
            if task.id:
                removed = self._remove_by_id(self.todo_file, task.id)
                if not removed:
                    removed = self._remove_by_id(self.done_file, task.id)

                if removed:
                    return

            # Fallback to original text
            original_text = getattr(task, "_original_text", None)
            if original_text:
                self._remove_from_file(self.todo_file, original_text)
                self._remove_from_file(self.done_file, original_text)
        except Exception as e:
            raise TaskRepositoryError(f"Failed to delete task: {e}") from e

    def _remove_by_id(self, file_path: Path, task_id: str) -> bool:
        """Helper to remove a task by ID from a file."""
        todotxt = TodoTxt(str(file_path))
        todotxt.parse()

        found = False
        to_remove = []

        for t in todotxt.tasks:
            attrs = getattr(t, "attributes", {})
            if not attrs:
                continue

            val = attrs.get("cmid")
            current_id = None
            if isinstance(val, list) and val:
                current_id = val[0]
            elif isinstance(val, str):
                current_id = val

            if current_id == task_id:
                to_remove.append(t)
                found = True

        if found:
            for t in to_remove:
                todotxt.tasks.remove(t)
            todotxt.save()
            return True
        return False

    def _remove_from_file(self, file_path: Path, task_str: str) -> bool:
        """Helper to remove a task string from a file."""
        todotxt = TodoTxt(str(file_path))
        todotxt.parse()

        found = False
        to_remove = []
        # We match by string representation
        for t in todotxt.tasks:
            if str(t) == task_str:
                to_remove.append(t)
                found = True

        if found:
            for t in to_remove:
                todotxt.tasks.remove(t)
            todotxt.save()
            return True
        return False
