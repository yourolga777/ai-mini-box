# How to add help to your plugin

Every plugin can provide its own help sections. They are merged with the core help and displayed in the web interface under "Help".

## 1. Add entry point in `pyproject.toml`

```toml
[project.entry-points."ai_mini_box.help"]
my_plugin = "my_ai_mini_box_plugin"
```

The value is the Python package name (any module in the package).

## 2. Create `help/` folder in your package

```
my_ai_mini_box_plugin/
├── __init__.py
├── commands.py
└── help/
    00-installation.md
    01-commands.md
```

## 3. Write Markdown files

Files are sorted alphabetically. Use `NN-` prefix to control order:

```markdown
# Plugin Name

Description of your plugin.

## Installation

```bash
pip install ai-mini-box-my-plugin
```

## Commands

| Command | Description |
|---|---|
| `ai-mini-box my-plugin cmd` | Does something |
```

## 4. Rules

- Use `# Title` for section headings — they become navigation anchors
- File must have `.md` extension
- Content is rendered as plain Markdown in the web interface
- Each file becomes a separate section in the "Help" page
- The `source` field shows "Plugin: my_plugin" to distinguish from core sections

## Example

See `ai-mini-box-telegram` package for a working example.
