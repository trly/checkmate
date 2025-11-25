"""Tests for TaskList filter functionality."""

from checkmate.models import Task
from checkmate.widgets.task_list import TaskList


class TestTaskListFilterState:
    """Tests for filter state management."""

    def test_initial_filter_state_empty(self):
        """TaskList starts with no filter applied."""
        task_list = TaskList()
        assert task_list.filter_contexts == set()
        assert task_list.filter_projects == set()
        assert not task_list.is_filtered

    def test_apply_filter_sets_state(self):
        """apply_filter sets the filter contexts and projects."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home", "work"], projects=["backend"])

        assert task_list.filter_contexts == {"home", "work"}
        assert task_list.filter_projects == {"backend"}
        assert task_list.is_filtered

    def test_apply_filter_with_empty_lists(self):
        """apply_filter with empty lists clears filter."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=["backend"])
        task_list.apply_filter(contexts=[], projects=[])

        assert task_list.filter_contexts == set()
        assert task_list.filter_projects == set()
        assert not task_list.is_filtered

    def test_clear_filter(self):
        """clear_filter removes all filter state."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=["backend"])
        task_list.clear_filter()

        assert task_list.filter_contexts == set()
        assert task_list.filter_projects == set()
        assert not task_list.is_filtered

    def test_is_filtered_only_contexts(self):
        """is_filtered is True when only contexts are set."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        assert task_list.is_filtered

    def test_is_filtered_only_projects(self):
        """is_filtered is True when only projects are set."""
        task_list = TaskList()
        task_list.apply_filter(contexts=[], projects=["backend"])
        assert task_list.is_filtered


class TestTaskListFilterLogic:
    """Tests for filter matching logic."""

    def test_task_matches_filter_no_filter(self):
        """Task matches when no filter is applied."""
        task_list = TaskList()
        task = Task(description="Buy groceries @home +shopping")
        assert task_list._task_matches_filter(task)

    def test_task_matches_context_filter(self):
        """Task matches when it has a matching context."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        task = Task(description="Buy groceries @home +shopping")
        assert task_list._task_matches_filter(task)

    def test_task_does_not_match_context_filter(self):
        """Task does not match when context doesn't match."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["work"], projects=[])
        task = Task(description="Buy groceries @home +shopping")
        assert not task_list._task_matches_filter(task)

    def test_task_matches_project_filter(self):
        """Task matches when it has a matching project."""
        task_list = TaskList()
        task_list.apply_filter(contexts=[], projects=["shopping"])
        task = Task(description="Buy groceries @home +shopping")
        assert task_list._task_matches_filter(task)

    def test_task_does_not_match_project_filter(self):
        """Task does not match when project doesn't match."""
        task_list = TaskList()
        task_list.apply_filter(contexts=[], projects=["backend"])
        task = Task(description="Buy groceries @home +shopping")
        assert not task_list._task_matches_filter(task)

    def test_task_matches_any_context_or_logic(self):
        """Task matches if it has ANY of the selected contexts (OR logic)."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home", "work", "phone"], projects=[])
        task = Task(description="Call mom @phone")
        assert task_list._task_matches_filter(task)

    def test_task_matches_any_project_or_logic(self):
        """Task matches if it has ANY of the selected projects (OR logic)."""
        task_list = TaskList()
        task_list.apply_filter(contexts=[], projects=["backend", "frontend", "devops"])
        task = Task(description="Fix API endpoint +backend")
        assert task_list._task_matches_filter(task)

    def test_task_matches_context_or_project(self):
        """Task matches if it has matching context OR project."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["work"], projects=["shopping"])
        # Task has @home (not work) but +shopping (matches)
        task = Task(description="Order supplies @home +shopping")
        assert task_list._task_matches_filter(task)

    def test_task_with_multiple_contexts_matches(self):
        """Task with multiple contexts matches if any context matches."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["work"], projects=[])
        task = Task(description="Meeting @work @office +project")
        assert task_list._task_matches_filter(task)

    def test_task_with_multiple_projects_matches(self):
        """Task with multiple projects matches if any project matches."""
        task_list = TaskList()
        task_list.apply_filter(contexts=[], projects=["frontend"])
        task = Task(description="Update styles +frontend +design")
        assert task_list._task_matches_filter(task)

    def test_task_no_tags_does_not_match_filter(self):
        """Task without any tags doesn't match when filter is active."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        task = Task(description="Simple task without tags")
        assert not task_list._task_matches_filter(task)


class TestTaskListFilteredClass:
    """Tests for the filtered CSS class."""

    def test_filtered_class_added_when_filter_applied(self):
        """CSS class 'filtered' is added when filter is applied."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        assert task_list.has_class("filtered")

    def test_filtered_class_not_present_initially(self):
        """CSS class 'filtered' is not present when no filter."""
        task_list = TaskList()
        assert not task_list.has_class("filtered")

    def test_filtered_class_removed_when_filter_cleared(self):
        """CSS class 'filtered' is removed when filter is cleared."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        task_list.clear_filter()
        assert not task_list.has_class("filtered")

    def test_filtered_class_removed_when_empty_filter_applied(self):
        """CSS class 'filtered' is removed when empty filter is applied."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        task_list.apply_filter(contexts=[], projects=[])
        assert not task_list.has_class("filtered")


class TestTaskListFilterPersistence:
    """Tests for filter persistence."""

    def test_filter_state_persists_after_apply(self):
        """Filter state persists after being applied."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home", "work"], projects=["backend"])

        # Check state is still there
        assert task_list.filter_contexts == {"home", "work"}
        assert task_list.filter_projects == {"backend"}
        assert task_list.is_filtered

    def test_filter_state_survives_multiple_applies(self):
        """Filter can be changed multiple times."""
        task_list = TaskList()
        task_list.apply_filter(contexts=["home"], projects=[])
        assert task_list.filter_contexts == {"home"}

        task_list.apply_filter(contexts=["work"], projects=["frontend"])
        assert task_list.filter_contexts == {"work"}
        assert task_list.filter_projects == {"frontend"}
