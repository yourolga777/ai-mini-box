# Package Setup

## pyproject.toml template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-my-plugin"
version = "0.1.0"
description = "My plugin for ai-mini-box"
requires-python = ">=3.12"
readme = "README.md"
license = { file = "LICENSE" }
dependencies = [
    "ai-mini-box-core>=5.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-mock>=3"]

[project.entry-points."ai_mini_box.tools"]
my_plugin = "ai_mini_box_my_plugin.commands:register"

[project.entry-points."ai_mini_box.help"]
my_plugin = "ai_mini_box_my_plugin"

[tool.hatch.build]
include = ["ai_mini_box_my_plugin/**"]
```

## Key points

- `name` must start with `ai-mini-box-` (the web UI filters by this pattern)
- `version` follows semver — bump on breaking changes to core or new features
- `ai-mini-box-core` is the only hard dependency
- Add extra deps your plugin needs (e.g., `requests`, `python-telegram-bot`)
- Entry point target is a `register` function in a Python module

## Entry points explained

```toml
[project.entry-points."ai_mini_box.tools"]
my_plugin = "ai_mini_box_my_plugin.commands:register"
```

This tells the core CLI: "call `register(app)` from `ai_mini_box_my_plugin.commands` when loading plugins". The `register` function receives a Typer instance and adds subcommands.

## Optional metadata

```toml
[project.urls]
Homepage = "https://github.com/your-org/ai-mini-box-my-plugin"
Repository = "https://github.com/your-org/ai-mini-box-my-plugin"

[project.classifiers]
"Development Status :: 4 - Beta"
"License :: OSI Approved :: MIT License"
"Programming Language :: Python :: 3.12"
"Programming Language :: Python :: 3.13"
```
