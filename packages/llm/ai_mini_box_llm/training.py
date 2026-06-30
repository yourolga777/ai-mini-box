from __future__ import annotations

import copy
import pickle
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .classifier import ClassifierEnsemble
from .models import TrainingLog


class Trainer:
    def __init__(self, classifier: ClassifierEnsemble, db_session_factory: Callable[[], Any]):
        self._classifier = classifier
        self._db = db_session_factory

    def log_correction(
        self,
        message_text: str,
        category_corrected: str,
        category_predicted: str | None = None,
        is_order_corrected: bool | None = None,
        is_order_predicted: bool | None = None,
    ) -> None:
        with self._db() as session:
            log = TrainingLog(
                message_text=message_text,
                category_predicted=category_predicted,
                category_corrected=category_corrected,
                is_order_predicted=is_order_predicted,
                is_order_corrected=is_order_corrected,
            )
            session.add(log)
            session.flush()

    def collect_batch(self, min_samples: int = 50) -> tuple[list[str], list[str]]:
        with self._db() as session:
            total = session.execute(select(func.count(TrainingLog.id))).scalar() or 0
            if total < min_samples:
                return [], []
            rows = session.execute(
                select(TrainingLog).where(TrainingLog.category_corrected.isnot(None))
                .order_by(TrainingLog.created_at.asc())
                .limit(min_samples)
            ).scalars().all()
            texts = [r.message_text for r in rows if r.message_text]
            categories = [r.category_corrected for r in rows if r.category_corrected]
            return texts, categories

    def train_on_batch(self, texts: list[str], categories: list[str]) -> dict[str, Any]:
        if not texts or not categories:
            return {"accuracy": 0.0, "trained": False, "samples": 0}

        split = int(len(texts) * 0.8)
        train_texts, test_texts = texts[:split], texts[split:]
        train_cats, test_cats = categories[:split], categories[split:]

        self._classifier.partial_fit_batch(train_texts, train_cats)

        correct = 0
        for t, c in zip(test_texts, test_cats):
            pred, _ = self._classifier.predict(t)
            if pred == c:
                correct += 1
        accuracy = correct / len(test_texts) if test_texts else 0.0

        logger.info("Trained on {} samples, accuracy: {:.1%}", len(train_texts), accuracy)
        return {"accuracy": round(accuracy, 4), "trained": True, "samples": len(train_texts)}

    def auto_train(self) -> dict[str, Any]:
        texts, categories = self.collect_batch(min_samples=50)
        if not texts:
            logger.info("Not enough training data (need 50, found fewer)")
            return {"accuracy": 0.0, "trained": False, "samples": 0}
        return self.train_on_batch(texts, categories)

    def nightly_retrain(
        self,
        backup_path: str = "data/classifier_model.backup.pkl",
        days: int = 30,
    ) -> dict[str, Any]:
        import datetime
        from ..models import Template

        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        with self._db() as session:
            rows = session.execute(
                select(TrainingLog).where(
                    TrainingLog.created_at >= cutoff,
                    TrainingLog.category_corrected.isnot(None),
                )
            ).scalars().all()

        if not rows:
            logger.info("No training data in last {} days", days)
            return {"accuracy": 0.0, "trained": False, "samples": 0}

        texts = [r.message_text for r in rows if r.message_text]
        categories = [r.category_corrected for r in rows if r.category_corrected]
        is_order = [bool(r.is_order_corrected) for r in rows if r.is_order_corrected is not None]

        backup = Path(backup_path)
        if self._classifier._fitted:
            try:
                self._classifier.save(str(backup))
                logger.info("Backed up old model to {}", backup_path)
            except Exception as e:
                logger.warning("Backup failed: {}", e)

        self._classifier.fit_all(texts, categories, is_order)
        self._classifier.save()

        correct = sum(1 for t, c in zip(texts, categories) if self._classifier.predict(t)[0] == c)
        accuracy = correct / len(texts) if texts else 0.0

        logger.info("Nightly retrain complete: {} samples, accuracy {:.1%}", len(texts), accuracy)
        return {"accuracy": round(accuracy, 4), "trained": True, "samples": len(texts)}
