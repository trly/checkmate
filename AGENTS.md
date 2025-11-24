## Build, Test, and Lint

```bash
# Run linting
uv run poe lint

# Run formatting
uv run poe format

# Run full check (lint + tests)
uv run poe check

# Run tests
uv run poe test

# Run specific test
uv run poe test tests/test_file.py

# Run app (development mode)
uv run poe tui

# Install dependencies
uv sync
```

## Project Structure

checkmate is a terminal user interface (TUI) client for todos.txt files using the Textual framework. Single-file entry point at `main.py`.

**Dependencies:**
- pytodotxt: todo.txt file format parsing
- textual: TUI framework for interactive terminal apps

## Code Style

- **Language**: Python 3.14+
- **No type hints or linting enforced** - add as project matures
- **Imports**: Standard library, then third-party (textual, pytodotxt)
- **Naming**: snake_case for functions, CamelCase for classes
- **Style**: Minimal - focus on clarity and functionality
- **Error handling**: Keep simple until error cases arise

## Library-Specific Patterns

### pytodotxt Attribute Access

Always use `.attributes.get()` to access task attributes:

```python
# ✅ Correct: Use .attributes.get()
due_values = task.attributes.get('due', [])  # Always returns a list

# ❌ Avoid: Bracket notation
due_values = task['due']  # Task objects are not subscriptable
```

The `.attributes.get()` method is the correct pytodotxt API - it's the only way to access custom metadata attributes on Task objects.

## Textual Development Patterns

### Input Fields with Labels

Always use explicit `Label` components instead of placeholder text for form inputs:

```python
# ✅ Correct: Use labels for clarity
yield Label("Description")
yield Input(id="task-input")
yield Label("Priority (A-Z)")
yield Input(id="priority-input", max_length=1)

# ❌ Avoid: Placeholder text
yield Input(id="task-input", placeholder="Enter task description")
```

Benefits:
- Clearer, more accessible UI
- Consistent styling with labels
- Placeholder text disappears when typing (less visible guidance)
- Labels remain visible for reference while editing

### Reactive DataTable Columns

To make DataTable columns resize dynamically with the terminal window:

1.  Implement a `rebuild_table()` method that:
    -   Calculates column widths based on `self.size.width`
    -   Saves the current cursor position
    -   Clears the table: `self.clear(columns=True)`
    -   Re-adds columns with calculated widths
    -   Re-populates rows
    -   Restores cursor position
2.  Call `rebuild_table()` in `on_resize(self, event)`
3.  Call `rebuild_table()` when data changes (instead of just adding rows)

Example:
```python
def on_resize(self, event) -> None:
    self.rebuild_table()

def rebuild_table(self) -> None:
    # Save cursor
    cursor = self.cursor_coordinate
    
    self.clear(columns=True)
    
    # Calculate widths
    width = self.size.width
    desc_width = width - 20  # Example calculation
    
    self.add_column("Description", width=desc_width)
    # ... add other columns ...
    
    # Add rows ...
    
    # Restore cursor
    self.move_cursor(row=cursor.row, column=cursor.column, animate=False)
    ```

    ### DataTable Cursor and Row Management

    **Critical: cursor_coordinate.row vs row_key from add_row()**
    - `cursor_coordinate.row` returns a visual row INDEX (integer: 0, 1, 2...)
    - `add_row()` returns an internal row_key (unique identifier, not an index)
    - These are NOT the same - don't confuse them!
    - To access data at cursor: maintain a parallel list/dict keyed by row index
    - Example (correct):
    ```python
    # In __init__
    self._task_by_row_index = []  # row_index -> Task mapping

    # In rebuild_table, after adding columns
    self._task_by_row_index = []
    for task in self._tasks:
    self.add_row(...)  # Ignore the return value
    self._task_by_row_index.append(task)

    # To get task at cursor
    def get_task_at_cursor(self):
    try:
        row_index = self.cursor_coordinate.row
        if 0 <= row_index < len(self._task_by_row_index):
            return self._task_by_row_index[row_index]
        return None
    except (ValueError, AttributeError):
        return None
    ```

    ## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**
```bash
bd ready --json
```

**Create new issues:**
```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**
```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**
```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`
6. **Commit together**: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state

### Auto-Sync

bd automatically syncs with git:
- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### MCP Server (Recommended)

If using Claude or MCP-compatible clients, install the beads MCP server:

```bash
pip install beads-mcp
```

Add to MCP config (e.g., `~/.config/claude/config.json`):
```json
{
"beads": {
  "command": "beads-mcp",
  "args": []
}
}
```

Then use `mcp__beads__*` functions instead of CLI commands.

### Managing AI-Generated Planning Documents

AI assistants often create planning and design documents during development:
- PLAN.md, IMPLEMENTATION.md, ARCHITECTURE.md
- DESIGN.md, CODEBASE_SUMMARY.md, INTEGRATION_PLAN.md
- TESTING_GUIDE.md, TECHNICAL_DESIGN.md, and similar files

**Best Practice: Use a dedicated directory for these ephemeral files**

**Recommended approach:**
- Create a `history/` directory in the project root
- Store ALL AI-generated planning/design docs in `history/`
- Keep the repository root clean and focused on permanent project files
- Only access `history/` when explicitly asked to review past planning

**Example .gitignore entry (optional):**
```
# AI planning documents (ephemeral)
history/
```

**Benefits:**
- ✅ Clean repository root
- ✅ Clear separation between ephemeral and permanent documentation
- ✅ Easy to exclude from version control if desired
- ✅ Preserves planning history for archeological research
- ✅ Reduces noise when browsing the project

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Store AI planning docs in `history/` directory
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT clutter repo root with planning documents

For more details, see README.md and QUICKSTART.md.
