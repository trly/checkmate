from datetime import date

import pytest

from checkmate.exceptions import TaskValidationError
from checkmate.repository import FileTaskRepository
from checkmate.services import TodoService


@pytest.fixture
def service(tmp_path):
    todo_file = tmp_path / "todo.txt"
    done_file = tmp_path / "done.txt"
    repo = FileTaskRepository(str(todo_file), str(done_file))
    return TodoService(repo)


def test_create_task(service):
    task = service.create_task("Buy milk")
    assert task.description == "Buy milk"
    assert task.creation_date == date.today()

    tasks = service.get_active_tasks()
    assert len(tasks) == 1
    assert tasks[0].description == "Buy milk"


def test_create_task_with_priority_and_due(service):
    task = service.create_task("Buy milk", priority="A", due_date=date(2025, 12, 31))
    assert task.priority == "A"
    assert task.due_date == date(2025, 12, 31)


def test_complete_task(service):
    task = service.create_task("Buy milk")
    service.complete_task(task)

    assert task.is_completed
    assert task.completion_date == date.today()

    incomplete = service.get_active_tasks()
    assert len(incomplete) == 0

    completed = service.get_completed_tasks()
    assert len(completed) == 1
    assert completed[0].description == "Buy milk"


def test_update_task(service):
    task = service.create_task("Buy milk")
    service.update_task(task, description="Buy cookies", priority="B")

    assert task.description == "Buy cookies"
    assert task.priority == "B"

    tasks = service.get_active_tasks()
    assert tasks[0].description == "Buy cookies"


def test_delete_task(service):
    task = service.create_task("Buy milk")
    service.delete_task(task)

    tasks = service.get_active_tasks()
    assert len(tasks) == 0


def test_create_task_validation(service):
    # Invalid priority
    with pytest.raises(
        TaskValidationError, match="Priority must be a single uppercase letter"
    ):
        service.create_task("Invalid priority", priority="AB")

    with pytest.raises(
        TaskValidationError, match="Priority must be a single uppercase letter"
    ):
        service.create_task("Invalid priority", priority="1")


def test_create_task_empty_description(service):
    with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
        service.create_task("")

    with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
        service.create_task("   ")

    task = service.create_task("Valid")
    with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
        service.update_task(task, description="")


def test_get_unique_contexts_empty(service):
    assert service.get_unique_contexts() == []


def test_get_unique_contexts(service):
    service.create_task("Task one @home @work")
    service.create_task("Task two @work @phone")
    service.create_task("Task three")

    contexts = service.get_unique_contexts()
    assert contexts == ["home", "phone", "work"]


def test_get_unique_contexts_excludes_completed(service):
    task = service.create_task("Task @home @work")
    service.create_task("Task @phone")
    service.complete_task(task)

    contexts = service.get_unique_contexts()
    assert contexts == ["phone"]


def test_get_unique_projects_empty(service):
    assert service.get_unique_projects() == []


def test_get_unique_projects(service):
    service.create_task("Task one +backend +frontend")
    service.create_task("Task two +frontend +mobile")
    service.create_task("Task three")

    projects = service.get_unique_projects()
    assert projects == ["backend", "frontend", "mobile"]


def test_get_unique_projects_excludes_completed(service):
    task = service.create_task("Task +backend +frontend")
    service.create_task("Task +mobile")
    service.complete_task(task)

    projects = service.get_unique_projects()
    assert projects == ["mobile"]
