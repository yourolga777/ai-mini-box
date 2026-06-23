from pathlib import Path

HELP_DIR = Path(__file__).resolve().parent.parent / "help"


def _read_md_files(directory: Path, source: str) -> list[dict]:
    if not directory.exists():
        return []
    sections = []
    for f in sorted(directory.iterdir()):
        if f.suffix == ".md":
            title = f.stem.split("_", 1)[-1].replace("-", " ").replace("_", " ").title()
            sections.append({
                "id": f.stem,
                "title": title,
                "content": f.read_text(encoding="utf-8"),
                "source": source,
                "order": len(sections),
            })
    return sections


def _get_plugin_help() -> list[dict]:
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return []
    sections = []
    for ep in entry_points(group="ai_mini_box.help"):
        try:
            module = ep.load()
            pkg_dir = Path(module.__file__).resolve().parent / "help"
            sections.extend(_read_md_files(pkg_dir, f"Plugin: {ep.name}"))
        except Exception:
            pass
    return sections


def get_all() -> list[dict]:
    sections = _read_md_files(HELP_DIR, "Core")
    sections.extend(_get_plugin_help())
    for i, sec in enumerate(sections):
        sec["order"] = i
    return sections
