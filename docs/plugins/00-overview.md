# Plugin Overview

A plugin (also called a service) is a Python package that integrates with ai-mini-box-core via entry points. It can add CLI commands, database logic, and help content to the web interface.

## Plugin structure

```
ai-mini-box-my-plugin/
├── ai_mini_box_my_plugin/
│   ├── __init__.py
│   ├── commands.py          # CLI commands (register function)
│   ├── help/                # Optional: help sections
│   │   00-installation.md
│   │   01-commands.md
│   └── ...
├── tests/
│   ├── __init__.py
│   └── test_commands.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Entry points

A plugin registers itself via two entry point groups:

| Group | Purpose |
|---|---|
| `ai_mini_box.tools` | Register CLI commands |
| `ai_mini_box.help`  | Provide help sections for web UI |

## Requirements

- Python ≥3.12
- Depends on `ai-mini-box-core>=5.0.0`
- Package name must follow `ai-mini-box-*` or `ai_mini_box_*` naming convention
- Build system: hatchling (recommended)
