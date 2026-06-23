# Web UI Plugin Management

The web interface provides a UI for managing plugins: install, uninstall, configure, and control daemons.

## How it works

The backend (`PluginManager` in `ai_mini_box_web.services.plugin_manager`) discovers installed plugins via the `ai_mini_box.tools` entry point group and exposes them through REST API endpoints.

## Install

Users can install plugins two ways:

### From PyPI

1. Go to Plugins → Install
2. Enter the package name (e.g., `ai-mini-box-telegram`)
3. Click Install

The backend runs `pip install` and then reloads the server to pick up the new entry points.

### Upload .whl

1. Go to Plugins → Install → Upload tab
2. Select a `.whl` file
3. Click Install

Only `.whl` files are accepted. The package name must match `^ai[-_]mini[-_]box[-_]`.

## Uninstall

- Core (`ai-mini-box-core`) and web (`ai-mini-box-web`) are **protected** and cannot be uninstalled via the UI
- Uninstalling removes the pip package and invalidates the entry point cache

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/plugins` | List all plugins |
| `GET` | `/api/plugins/{name}` | Get plugin details (status, PID) |
| `GET` | `/api/plugins/{name}/logs` | Get recent log lines |
| `POST` | `/api/plugins/install` | Install from PyPI |
| `POST` | `/api/plugins/install/upload` | Install from .whl upload |
| `DELETE` | `/api/plugins/{name}` | Uninstall plugin |
| `POST` | `/api/plugins/{name}/start` | Start daemon process |
| `POST` | `/api/plugins/{name}/stop` | Stop daemon process |
| `POST` | `/api/plugins/{name}/action` | Run plugin action (e.g., `poll`) |
| `GET` | `/api/plugins/config` | Get configuration |
| `POST` | `/api/plugins/config/set` | Set a config value |

## Daemon lifecycle

When **Start daemon** is clicked:

1. The backend spawns `python -m ai_mini_box <name> daemon` as a subprocess
2. stdout/stderr are appended to `logs/plugin_<name>.log`
3. The PID is saved to `data/daemon_pids.json`
4. On server restart, PIDs are checked against running processes

When **Stop daemon** is clicked:

- Unix: sends `SIGTERM`, then `SIGKILL` after 2s if still running
- Windows: runs `taskkill /F /PID <pid>`

## Server reload

After installing a plugin, the server reloads itself via `os.execv` after a 2-second delay. This is required for the new entry points to be discovered. All daemon PIDs survive the restart (they're stored on disk).
