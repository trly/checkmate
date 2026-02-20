import os
from pathlib import Path


def load_config(content: str) -> dict[str, str]:
    """
    Parse .todo/config file using standard KEY=VALUE format.

    Ignores:
    - Lines starting with # (comments)
    - Empty lines
    - Lines without = separator

    Args:
        content: Raw config file content as string

    Returns:
        Dictionary mapping keys to values
    """
    config = {}

    for line in content.splitlines():
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Skip lines without = separator
        if "=" not in line:
            continue

        # Split on first = only
        key, value = line.split("=", 1)
        config[key.strip()] = value

    return config


def discover_files(
    cli_todo_file: str | None = None,
    cli_done_file: str | None = None,
    config: dict[str, str] | None = None,
) -> tuple[str, str]:
    """
    Discover todo and done file paths with proper precedence.

    Precedence (highest to lowest):
    1. Command-line arguments
    2. Configuration from .todo/config
    3. Default paths ($HOME/todo.txt and $HOME/done.txt)

    Resolves all symlinks to canonical paths.
    Returns paths even if files don't exist yet.

    Args:
        cli_todo_file: Path from command-line argument (highest precedence)
        cli_done_file: Path from command-line argument (highest precedence)
        config: Configuration dictionary from .todo/config

    Returns:
        Tuple of (todo_file_path, done_file_path) with symlinks resolved
    """
    config = config or {}
    home = os.path.expanduser("~")

    # Determine todo file path
    if cli_todo_file:
        todo_file = cli_todo_file
    elif "TODO_FILE" in config:
        todo_file = config["TODO_FILE"]
    else:
        todo_file = os.path.join(home, "todo.txt")

    # Determine done file path
    if cli_done_file:
        done_file = cli_done_file
    elif "DONE_FILE" in config:
        done_file = config["DONE_FILE"]
    else:
        done_file = os.path.join(home, "done.txt")

    # Resolve symlinks to canonical paths
    todo_file = os.path.realpath(todo_file)
    done_file = os.path.realpath(done_file)

    return todo_file, done_file


def load_config_file(home_dir: str | None = None) -> dict[str, str]:
    """
    Load configuration from .todo/config file in home directory.

    Returns empty dict if file doesn't exist.

    Args:
        home_dir: Override home directory (useful for testing)

    Returns:
        Configuration dictionary, empty if file doesn't exist
    """
    if home_dir is None:
        home_dir = os.path.expanduser("~")

    config_path = os.path.join(home_dir, ".todo", "config")

    if not os.path.exists(config_path):
        return {}

    try:
        content = Path(config_path).read_text()
        return load_config(content)
    except OSError:
        return {}


VALID_SORT_ATTRIBUTES = frozenset({"priority", "context", "project", "due", "created"})


def save_config_value(
    key: str, value: str, home_dir: str | None = None
) -> None:
    """
    Save a single key=value pair to the .todo/config file.

    Updates the key in-place if it exists, otherwise appends it.
    Creates the file and directory if they don't exist.

    Args:
        key: Configuration key to set
        value: Configuration value to set
        home_dir: Override home directory (useful for testing)
    """
    if home_dir is None:
        home_dir = os.path.expanduser("~")

    config_dir = Path(home_dir) / ".todo"
    config_path = config_dir / "config"

    # Read existing lines (preserving comments and structure)
    lines: list[str] = []
    if config_path.exists():
        try:
            lines = config_path.read_text().splitlines()
        except OSError:
            lines = []

    # Try to update existing key in-place
    updated = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            existing_key, _ = stripped.split("=", 1)
            if existing_key.strip() == key:
                lines[i] = f"{key}={value}"
                updated = True
                break

    if not updated:
        lines.append(f"{key}={value}")

    # Write back
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text("\n".join(lines) + "\n")
