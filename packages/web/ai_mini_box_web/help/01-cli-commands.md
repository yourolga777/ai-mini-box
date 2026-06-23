# CLI Commands

## Main commands

| Command | Description |
|---|---|
| `ai-mini-box init` | Create config and database |
| `ai-mini-box check-db` | Verify database connection |
| `ai-mini-box db upgrade` | Run pending migrations |
| `ai-mini-box config show` | Display configuration |
| `ai-mini-box config set <key> <value>` | Set a config value |
| `ai-mini-box config unset <key>` | Reset to default value |
| `ai-mini-box serve` | Start web interface |

## Plugin commands

Plugins register their own commands via entry points. For example, after installing `ai-mini-box-telegram`:

```bash
ai-mini-box telegram poll
ai-mini-box telegram daemon
```

Run `ai-mini-box --help` to see all available commands.

## Global options

- `--verbose` — detailed output
- `--log-file <path>` — write logs to file
- `--help` — show help for any command
