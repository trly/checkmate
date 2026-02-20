"""Tests for config persistence."""

from checkmate.config import VALID_SORT_ATTRIBUTES, load_config, save_config_value


def test_save_config_value_creates_file(tmp_path):
    """save_config_value creates .todo/config when it doesn't exist."""
    save_config_value("SORT_ATTRIBUTE", "priority", home_dir=str(tmp_path))

    config_path = tmp_path / ".todo" / "config"
    assert config_path.exists()

    config = load_config(config_path.read_text())
    assert config["SORT_ATTRIBUTE"] == "priority"


def test_save_config_value_updates_existing_key(tmp_path):
    """save_config_value updates an existing key in-place."""
    config_dir = tmp_path / ".todo"
    config_dir.mkdir()
    config_path = config_dir / "config"
    config_path.write_text("TODO_FILE=/home/user/todo.txt\nSORT_ATTRIBUTE=context\n")

    save_config_value("SORT_ATTRIBUTE", "due", home_dir=str(tmp_path))

    config = load_config(config_path.read_text())
    assert config["SORT_ATTRIBUTE"] == "due"
    assert config["TODO_FILE"] == "/home/user/todo.txt"


def test_save_config_value_appends_new_key(tmp_path):
    """save_config_value appends a new key without disturbing existing content."""
    config_dir = tmp_path / ".todo"
    config_dir.mkdir()
    config_path = config_dir / "config"
    config_path.write_text("TODO_FILE=/home/user/todo.txt\n")

    save_config_value("SORT_ATTRIBUTE", "project", home_dir=str(tmp_path))

    config = load_config(config_path.read_text())
    assert config["SORT_ATTRIBUTE"] == "project"
    assert config["TODO_FILE"] == "/home/user/todo.txt"


def test_save_config_value_preserves_comments(tmp_path):
    """save_config_value preserves comments and blank lines."""
    config_dir = tmp_path / ".todo"
    config_dir.mkdir()
    config_path = config_dir / "config"
    config_path.write_text("# My config\nTODO_FILE=/home/user/todo.txt\n")

    save_config_value("SORT_ATTRIBUTE", "priority", home_dir=str(tmp_path))

    content = config_path.read_text()
    assert "# My config" in content
    assert "SORT_ATTRIBUTE=priority" in content


def test_valid_sort_attributes_contains_expected_values():
    """VALID_SORT_ATTRIBUTES contains all expected sort attributes."""
    assert VALID_SORT_ATTRIBUTES == {"priority", "context", "project", "due", "created"}
