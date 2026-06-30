from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Template


class SystemTemplateSync:
    def __init__(self, db_session_factory: Callable[[], Session], config_path: str = "data/business_config.json"):
        self._db = db_session_factory
        self._config_path = Path(config_path)

    def sync_on_startup(self) -> None:
        if not self._config_path.exists():
            logger.info("No business_config.json found, skipping system template sync")
            return
        try:
            config = json.loads(self._config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read business_config.json: {}", e)
            return

        templates: dict[str, Any] = config.get("templates", {}).get("system", {})
        if not templates:
            return

        with self._db() as session:
            existing = session.execute(
                select(Template).where(Template.scope == "system")
            ).scalars().all()
            existing_map = {t.slug: t for t in existing}
            config_slugs = set()

            for slug, data in templates.items():
                config_slugs.add(slug)
                text = data.get("text", "")
                category = data.get("category", "question")
                triggers = data.get("triggers", [])
                name = data.get("name", slug)

                if slug in existing_map:
                    t = existing_map[slug]
                    if t.text != text:
                        t.text = text
                        t.version += 1
                        logger.info("Updated system template: {} (v{})", slug, t.version)
                else:
                    t = Template(
                        scope="system",
                        category=category,
                        name=name,
                        slug=slug,
                        text=text,
                        is_active=1,
                        is_archived=0,
                    )
                    t.triggers = triggers
                    session.add(t)
                    logger.info("Created system template: {}", slug)

            for slug, t in existing_map.items():
                if slug not in config_slugs and not t.is_archived:
                    t.is_archived = 1
                    t.is_active = 0
                    logger.info("Archived removed system template: {}", slug)

            session.flush()
