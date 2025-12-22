"""Tests for the confirm modal screen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button

from checkmate.screens.confirm import ConfirmScreen


@pytest.mark.asyncio
async def test_confirm_screen_compose():
    """Test that ConfirmScreen composes with Yes and No buttons."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ConfirmScreen(message="Are you sure?")

    app = TestApp()
    async with app.run_test() as _:
        screen = app.query_one(ConfirmScreen)
        assert screen is not None

        yes_btn = app.query_one("#yes-btn", Button)
        no_btn = app.query_one("#no-btn", Button)

        assert yes_btn is not None
        assert no_btn is not None


@pytest.mark.asyncio
async def test_confirm_screen_default_message():
    """Test that ConfirmScreen uses default message."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ConfirmScreen()

    app = TestApp()
    async with app.run_test() as _:
        screen = app.query_one(ConfirmScreen)
        assert screen.message == "Are you sure?"


@pytest.mark.asyncio
async def test_confirm_screen_yes_returns_true():
    """Test Yes button dismisses screen with True."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                ConfirmScreen(message="Delete this?"),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # Wait for screen to mount
        screen = app.screen
        yes_btn = screen.query_one("#yes-btn", Button)
        yes_btn.press()
        await pilot.pause()

        assert app.dismiss_result is True


@pytest.mark.asyncio
async def test_confirm_screen_no_returns_false():
    """Test No button dismisses screen with False."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                ConfirmScreen(message="Delete this?"),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # Wait for screen to mount
        screen = app.screen
        no_btn = screen.query_one("#no-btn", Button)
        no_btn.press()
        await pilot.pause()

        assert app.dismiss_result is False


@pytest.mark.asyncio
async def test_confirm_screen_keyboard_y_confirms():
    """Test that 'y' key confirms (returns True)."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                ConfirmScreen(message="Continue?"),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        assert app.dismiss_result is True


@pytest.mark.asyncio
async def test_confirm_screen_keyboard_n_cancels():
    """Test that 'n' key cancels (returns False)."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                ConfirmScreen(message="Continue?"),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        assert app.dismiss_result is False


@pytest.mark.asyncio
async def test_confirm_screen_escape_cancels():
    """Test that Escape key cancels (returns False)."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.dismiss_result = None

        async def on_mount(self):
            def capture_result(result):
                self.dismiss_result = result

            await self.push_screen(
                ConfirmScreen(message="Continue?"),
                callback=capture_result,
            )

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert app.dismiss_result is False
