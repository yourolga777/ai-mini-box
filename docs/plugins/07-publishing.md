# Publishing

## Building

```bash
pip install build
cd packages/my-plugin
python -m build
```

This creates `dist/ai_mini_box_my_plugin-0.1.0.tar.gz` and `.whl`.

## Publishing to PyPI

```bash
pip install twine
twine upload dist/*
```

Or use GitHub Actions (see `.github/workflows/publish.yml` in the core repo for reference):

```yaml
name: Publish to PyPI
on:
  push:
    tags:
      - "my-plugin-v*"
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install hatchling build
      - run: python -m build
        working-directory: packages/my-plugin
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          user: __token__
          password: ${{ secrets.PYPI_TOKEN }}
          packages-dir: packages/my-plugin/dist
```

## Versioning

Follow semantic versioning:

- **Major** — breaking changes to core integration
- **Minor** — new features, backwards compatible
- **Patch** — bug fixes

The core packages (`ai-mini-box-core`, `ai-mini-box-web`) have independent version cycles. Your plugin should specify a minimum core version:

```toml
dependencies = [
    "ai-mini-box-core>=5.0.0",
]
```

## Pre-release checklist

- [ ] Tests pass (`python -m pytest tests/ -v`)
- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated (if you maintain one)
- [ ] `README.md` has install/usage instructions
- [ ] `LICENSE` file present (MIT recommended)
- [ ] Help sections updated in `help/` directory
- [ ] Built and tested locally: `pip install dist/*.whl`

## Catalog registration

After publishing, register your plugin in the core catalog so users see it in `ai-mini-box plugin catalog`:

1. Edit `packages/core/ai_mini_box/data/plugin-catalog.json` in the core repo
2. Add your entry following the existing format:
   ```json
   {
     "name": "weather",
     "title": "Weather",
     "description": "Прогноз погоды и уведомления о непогоде",
     "package": "ai-mini-box-weather",
     "min_core": "5.0.0",
     "url": "https://github.com/your-org/ai-mini-box-weather"
   }
   ```
3. Open a PR to the core repository with this change

The `name` must match your entry point name. The `package` must match your PyPI package name.

## Package naming

| Type | Package name | Entry point name |
|---|---|---|
| Core | `ai-mini-box-core` | — |
| Web | `ai-mini-box-web` | `web` |
| Telegram | `ai-mini-box-telegram` | `telegram` |
| Your plugin | `ai-mini-box-<name>` | `<name>` |

The entry point name becomes the identifier in the web UI.
