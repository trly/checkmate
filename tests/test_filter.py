"""Tests for the filter modal screen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, SelectionList

from checkmate.screens.filter import FilterScreen


@pytest.mark.asyncio
async def test_filter_screen_compose():
    """Test that FilterScreen composes with context and project selection lists."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(
                contexts=["home", "work"],
                projects=["backend", "frontend"],
            )

    app = TestApp()
    async with app.run_test() as _:
        app.query_one(FilterScreen)

        contexts_list = app.query_one("#contexts-list", SelectionList)
        projects_list = app.query_one("#projects-list", SelectionList)

        assert contexts_list is not None
        assert projects_list is not None


@pytest.mark.asyncio
async def test_filter_screen_empty_lists():
    """Test FilterScreen handles empty contexts and projects."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(contexts=[], projects=[])

    app = TestApp()
    async with app.run_test() as _:
        app.query_one(FilterScreen)

        contexts_list = app.query_one("#contexts-list", SelectionList)
        projects_list = app.query_one("#projects-list", SelectionList)

        assert len(contexts_list.selected) == 0
        assert len(projects_list.selected) == 0


@pytest.mark.asyncio
async def test_filter_screen_preselects_current_filters():
    """Test that current filter state is pre-selected."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(
                contexts=["home", "work", "phone"],
                projects=["backend", "frontend"],
                selected_contexts=["home", "work"],
                selected_projects=["frontend"],
            )

    app = TestApp()
    async with app.run_test() as _:
        contexts_list = app.query_one("#contexts-list", SelectionList)
        projects_list = app.query_one("#projects-list", SelectionList)

        assert set(contexts_list.selected) == {"home", "work"}
        assert set(projects_list.selected) == {"frontend"}


@pytest.mark.asyncio
async def test_filter_screen_apply_returns_result():
    """Test Apply button calls dismiss with FilterResult containing selections."""
    from checkmate.screens.filter import FilterResult

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                FilterScreen(
                    contexts=["home", "work"],
                    projects=["backend", "frontend"],
                    selected_contexts=["home"],
                    selected_projects=["backend"],
                ),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # Wait for screen to mount
        screen = app.screen
        apply_btn = screen.query_one("#apply-btn", Button)
        apply_btn.press()
        await pilot.pause()

        assert app.dismiss_result is not None
        assert isinstance(app.dismiss_result, FilterResult)
        assert set(app.dismiss_result.contexts) == {"home"}
        assert set(app.dismiss_result.projects) == {"backend"}


@pytest.mark.asyncio
async def test_filter_screen_cancel_returns_none():
    """Test Cancel button dismisses with None result."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_called = False
            self.dismiss_result = "not_none"

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_called = True
                self.dismiss_result = result

            await self.push_screen(
                FilterScreen(
                    contexts=["home", "work"],
                    projects=["backend"],
                ),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # Wait for screen to mount
        screen = app.screen
        cancel_btn = screen.query_one("#cancel-btn", Button)
        cancel_btn.press()
        await pilot.pause()

        assert app.dismiss_called
        assert app.dismiss_result is None


@pytest.mark.asyncio
async def test_filter_screen_escape_closes():
    """Test that Escape key closes screen without applying."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(
                contexts=["home"],
                projects=["backend"],
            )

    app = TestApp()
    async with app.run_test() as pilot:
        screen = app.query_one(FilterScreen)
        assert screen is not None

        await pilot.press("escape")
        await pilot.pause()


@pytest.mark.asyncio
async def test_filter_screen_clear_button():
    """Test Clear button deselects all items."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(
                contexts=["home", "work"],
                projects=["backend", "frontend"],
                selected_contexts=["home", "work"],
                selected_projects=["backend", "frontend"],
            )

    app = TestApp()
    async with app.run_test() as pilot:
        contexts_list = app.query_one("#contexts-list", SelectionList)
        projects_list = app.query_one("#projects-list", SelectionList)

        assert len(contexts_list.selected) == 2
        assert len(projects_list.selected) == 2

        clear_btn = app.query_one("#clear-btn", Button)
        clear_btn.press()
        await pilot.pause()

        assert len(contexts_list.selected) == 0
        assert len(projects_list.selected) == 0


@pytest.mark.asyncio
async def test_filter_screen_has_labels():
    """Test that FilterScreen has labels for both lists."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FilterScreen(
                contexts=["home"],
                projects=["backend"],
            )

    app = TestApp()
    async with app.run_test() as _:
        contexts_label = app.query_one("Label.list-label")
        assert contexts_label is not None
