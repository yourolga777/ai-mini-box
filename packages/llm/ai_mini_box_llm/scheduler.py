from __future__ import annotations

import datetime
import logging
from typing import Any

from typing import Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlalchemy import Engine

from ai_mini_box.core.services.registry import get_service

log = logging.getLogger("apscheduler")
log.setLevel(logging.WARNING)


def _job_nightly_retrain():
    trainer = get_service("trainer")
    if trainer is None:
        logger.warning("nightly_retrain: trainer not available")
        return
    try:
        metrics = trainer.nightly_retrain()
        logger.info("nightly_retrain complete: {}", metrics)
    except Exception as e:
        logger.exception("nightly_retrain failed: {}", e)


def _job_sync_templates():
    sync = get_service("system_template_sync")
    if sync is None:
        logger.warning("sync_templates: SystemTemplateSync not available")
        return
    try:
        sync.sync_on_startup()
        logger.info("sync_templates: system templates synced")
    except Exception as e:
        logger.exception("sync_templates failed: {}", e)


def _job_rebuild_rag_index():
    pipeline = get_service("llm")
    if pipeline is None:
        logger.warning("rebuild_rag_index: pipeline not available")
        return
    try:
        count = pipeline._rag.rebuild_index([], [])
        logger.info("rebuild_rag_index: done ({} entries)", count)
    except Exception as e:
        logger.exception("rebuild_rag_index failed: {}", e)


def _job_cleanup_logs():
    from ai_mini_box.infrastructure.database import get_db as _get_db
    from ai_mini_box_llm.models import TrainingLog

    cutoff = datetime.datetime.now() - datetime.timedelta(days=90)
    try:
        with _get_db() as session:
            from sqlalchemy import delete
            result = session.execute(
                delete(TrainingLog).where(TrainingLog.created_at < cutoff)
            )
            session.flush()
            logger.info("cleanup_logs: deleted {} old training logs", result.rowcount)
    except Exception as e:
        logger.exception("cleanup_logs failed: {}", e)


class TaskScheduler:
    def __init__(self, db_url: str = "", engine: Optional[Engine] = None):
        jobstore = SQLAlchemyJobStore(engine=engine) if engine else SQLAlchemyJobStore(url=db_url)
        self._scheduler = BackgroundScheduler(
            jobstores={"default": jobstore},
            executors={"default": ThreadPoolExecutor(max_workers=2)},
            timezone="Europe/Moscow",
        )

    def setup(self):
        self._scheduler.add_job(
            func="ai_mini_box_llm.scheduler:_job_nightly_retrain",
            trigger=CronTrigger(hour=2, minute=0),
            id="nightly_retrain",
            max_instances=1,
            misfire_grace_time=3600,
            replace_existing=True,
        )
        self._scheduler.add_job(
            func="ai_mini_box_llm.scheduler:_job_sync_templates",
            trigger=CronTrigger(minute=0),
            id="sync_templates",
            max_instances=1,
            replace_existing=True,
        )
        self._scheduler.add_job(
            func="ai_mini_box_llm.scheduler:_job_rebuild_rag_index",
            trigger=CronTrigger(hour="*/6", minute=0),
            id="rebuild_rag_index",
            max_instances=1,
            replace_existing=True,
        )
        self._scheduler.add_job(
            func="ai_mini_box_llm.scheduler:_job_cleanup_logs",
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),
            id="cleanup_logs",
            max_instances=1,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("TaskScheduler started: 4 jobs registered")

    def shutdown(self):
        try:
            self._scheduler.shutdown(wait=False)
            logger.info("TaskScheduler shut down")
        except Exception:
            pass
