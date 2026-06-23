# Help Sections

Your plugin can provide help content that appears in the web interface's "Help" page.

## 1. Add entry point

```toml
# pyproject.toml
[project.entry-points."ai_mini_box.help"]
my_plugin = "ai_mini_box_my_plugin"
```

The value is the importable package name (any module inside your package).

## 2. Create help directory

```
ai_mini_box_my_plugin/
├── __init__.py
├── commands.py
└── help/
    00-installation.md
    01-commands.md
    02-troubleshooting.md
```

## 3. Write Markdown

Files use standard Markdown. Each file becomes a section in the Help page.

```markdown
# Installation

## Requirements
- ai-mini-box-core >= 5.0.0

## Install

```bash
pip install ai-mini-box-my-plugin
```

## Configuration

```bash
ai-mini-box config set my_plugin_key value
```
```

## Rules

- File names must end with `.md`
- Use `# Title` for headings — they become navigation anchors
- Use code fences with language for syntax highlighting
- Tables, lists, links, and inline code are supported
- The `source` label shows "Plugin: my_plugin" to distinguish from core help

## Order control

Prefix files with `NN-` where NN is a two-digit number:

```
00-installation.md
01-commands.md
02-api.md
```

Sections from different plugins are merged in alphabetical order by source name.
