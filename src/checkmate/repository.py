from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from pytodotxt import Task as PytodoTask
from pytodotxt import TodoTxt

from .models import Task


class TaskRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Task]:
        """Get all tasks."""
        pass

    @abstractmethod
    def get_archived(self) -> List[Task]:
        """Get all archived (completed) tasks."""
        pass

    @abstractmethod
    def save(self, task: Task) -> None:
        """Save a task (create or update)."""
        pass

    @abstractmethod
    def delete(self, task: Task) -> None:
        """Delete a task."""
        pass


class FileTaskRepository(TaskRepository):
    def __init__(self, todo_file: str, done_file: str):
        self.todo_file = Path(todo_file)
        self.done_file = Path(done_file)
        self._ensure_files_exist()

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

        task = Task(
            description=pytodo_task.description or "",
            is_completed=pytodo_task.is_completed or False,
            priority=pytodo_task.priority,
            creation_date=pytodo_task.creation_date,
            completion_date=pytodo_task.completion_date,
            projects=pytodo_task.projects if hasattr(pytodo_task, "projects") else [],
            contexts=pytodo_task.contexts if hasattr(pytodo_task, "contexts") else [],
            attributes=attrs,
            _original_text=str(pytodo_task),
        )
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

    def get_all(self) -> List[Task]:
        """Get all active tasks from todo.txt."""
        todotxt = TodoTxt(str(self.todo_file))
        todotxt.parse()
        return [self._to_domain(t) for t in todotxt.tasks]

    def get_archived(self) -> List[Task]:
        """Get all completed tasks from done.txt."""
        donetxt = TodoTxt(str(self.done_file))
        donetxt.parse()
        return [self._to_domain(t) for t in donetxt.tasks]

    def save(self, task: Task) -> None:
        """Save a task (create or update)."""
        pytodo_task = self._to_pytodo(task)
        new_text = str(pytodo_task)

        # If we have original text, try to find and remove it first (Update scenario)
        if task._original_text:
            # Check if the text actually changed to avoid unnecessary IO
            if task._original_text == new_text:
                # However, we might be moving files (completing/uncompleting)
                # So we still need to check logic below
                pass

            # Try to remove from both files to be safe (in case it moved)
            self._remove_from_file(self.todo_file, task._original_text)
            self._remove_from_file(self.done_file, task._original_text)

        # Determine target file based on current state
        target_file = self.done_file if task.is_completed else self.todo_file

        # Add to target file
        todotxt = TodoTxt(str(target_file))
        todotxt.parse()
        todotxt.tasks.append(pytodo_task)
        todotxt.save()

        # Update original text for future updates
        task._original_text = new_text

    def delete(self, task: Task) -> None:
        """Delete a task."""
        if task._original_text:
            self._remove_from_file(self.todo_file, task._original_text)
            self._remove_from_file(self.done_file, task._original_text)

    def _remove_from_file(self, file_path: Path, task_str: str) -> bool:
        """Helper to remove a task string from a file."""
        try:
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
        except Exception:
            return False