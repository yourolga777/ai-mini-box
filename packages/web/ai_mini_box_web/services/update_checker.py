import json
import urllib.request
from importlib.metadata import version

from loguru import logger


def check_pypi_update(package: str) -> str | None:
    try:
        installed = version(package)
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            latest = json.loads(resp.read())["info"]["version"]
        if latest != installed:
            return latest
    except Exception:
        pass
    return None


def warn_updates(*packages: str):
    for pkg in packages:
        latest = check_pypi_update(pkg)
        if latest:
            logger.warning(
                "Update available: {} {} → {}. Run: pip install --upgrade {}",
                pkg,
                version(pkg),
                latest,
                pkg,
            )
