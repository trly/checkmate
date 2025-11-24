from datetime import date

import pytest

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

    tasks = service.get_incomplete_tasks()
    assert len(tasks) == 1
    assert tasks[0].description == "Buy milk"


def test_create_task_with_priority_and_due(service):
    task = service.create_task("Buy milk", priority="A", due_date="2025-12-31")
    assert task.priority == "A"
    assert task.due_date == date(2025, 12, 31)


def test_complete_task(service):
    task = service.create_task("Buy milk")
    service.complete_task(task)

    assert task.is_completed
    assert task.completion_date == date.today()

    incomplete = service.get_incomplete_tasks()
    assert len(incomplete) == 0

    completed = service.get_completed_tasks()
    assert len(completed) == 1
    assert completed[0].description == "Buy milk"


def test_update_task(service):
    task = service.create_task("Buy milk")
    service.update_task(task, description="Buy cookies", priority="B")

    assert task.description == "Buy cookies"
    assert task.priority == "B"

    tasks = service.get_incomplete_tasks()
    assert tasks[0].description == "Buy cookies"


def test_delete_task(service):
    task = service.create_task("Buy milk")
    service.delete_task(task)

    tasks = service.get_incomplete_tasks()
    assert len(tasks) == 0
