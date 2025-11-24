import pytest

from checkmate.models import Task
from checkmate.repository import FileTaskRepository, TaskRepositoryError


@pytest.fixture
def repo(tmp_path):
    todo_file = tmp_path / "todo.txt"
    done_file = tmp_path / "done.txt"
    return FileTaskRepository(str(todo_file), str(done_file))


def test_repository_raises_error_on_io_failure(repo, tmp_path):
    # Make file read-only to trigger IO error
    p = tmp_path / "todo.txt"
    p.touch()
    p.chmod(0o000)

    try:
        with pytest.raises(TaskRepositoryError):
            repo.get_active_tasks()
    finally:
        p.chmod(0o666)  # restore


def test_repository_validates_distinct_paths(tmp_path):
    f = tmp_path / "tasks.txt"
    with pytest.raises(ValueError, match="distinct"):
        FileTaskRepository(str(f), str(f))


def test_repository_validates_accessibility(tmp_path):
    # Create a directory that is read-only
    d = tmp_path / "readonly"
    d.mkdir()
    try:
        # Remove write permission
        d.chmod(0o444)

        # Attempt to create files inside readonly dir
        with pytest.raises(ValueError, match="accessible"):
            FileTaskRepository(str(d / "todo.txt"), str(d / "done.txt"))
    finally:
        # Restore permission to allow cleanup
        d.chmod(0o777)


def test_save_generates_id(repo, tmp_path):
    task = Task("Test task")
    repo.save(task)

    # Verify task has an ID in attributes
    assert "cmid" in task.attributes

    # Verify ID is persisted to file
    content = (tmp_path / "todo.txt").read_text()
    assert f"cmid:{task.attributes['cmid']}" in content


def test_id_is_stable(repo):
    task = Task("Test task")
    repo.save(task)
    initial_id = task.attributes["cmid"]

    task.description = "Updated task"
    repo.save(task)

    assert task.attributes["cmid"] == initial_id
