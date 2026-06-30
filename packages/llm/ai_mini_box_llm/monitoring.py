from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from loguru import logger
from sqlalchemy import func, select

from .models import TrainingLog


class DriftMonitor:
    def __init__(self, db_session_factory: Callable[[], Any]):
        self._db = db_session_factory

    def compute_accuracy(self, since_hours: int = 168) -> float:
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=since_hours)
        with self._db() as session:
            rows = session.execute(
                select(TrainingLog).where(
                    TrainingLog.created_at >= cutoff,
                    TrainingLog.category_corrected.isnot(None),
                    TrainingLog.category_predicted.isnot(None),
                )
            ).scalars().all()
        if not rows:
            return 0.0
        correct = sum(1 for r in rows if r.category_predicted == r.category_corrected)
        return round(correct / len(rows), 4)

    def confusion_matrix(self, since_hours: int = 168) -> dict[str, dict[str, int]]:
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=since_hours)
        with self._db() as session:
            rows = session.execute(
                select(TrainingLog).where(
                    TrainingLog.created_at >= cutoff,
                    TrainingLog.category_corrected.isnot(None),
                    TrainingLog.category_predicted.isnot(None),
                )
            ).scalars().all()
        matrix: dict[str, dict[str, int]] = {}
        for r in rows:
            pred = r.category_predicted or "?"
            corr = r.category_corrected or "?"
            if corr not in matrix:
                matrix[corr] = {}
            matrix[corr][pred] = matrix[corr].get(pred, 0) + 1
        return matrix

    def category_distribution(self, since_hours: int = 168) -> dict[str, int]:
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=since_hours)
        with self._db() as session:
            rows = session.execute(
                select(TrainingLog.category_corrected).where(
                    TrainingLog.created_at >= cutoff,
                    TrainingLog.category_corrected.isnot(None),
                )
            ).scalars().all()
        return dict(Counter(rows))

    def accuracy_trend(self, days: int = 30) -> list[dict[str, Any]]:
        import datetime
        trend: list[dict[str, Any]] = []
        for i in range(days):
            day_start = datetime.datetime.now() - datetime.timedelta(days=i + 1)
            day_end = datetime.datetime.now() - datetime.timedelta(days=i)
            with self._db() as session:
                rows = session.execute(
                    select(TrainingLog).where(
                        TrainingLog.created_at >= day_start,
                        TrainingLog.created_at < day_end,
                        TrainingLog.category_corrected.isnot(None),
                        TrainingLog.category_predicted.isnot(None),
                    )
                ).scalars().all()
            if rows:
                correct = sum(1 for r in rows if r.category_predicted == r.category_corrected)
                trend.append({
                    "date": day_start.date().isoformat(),
                    "accuracy": round(correct / len(rows), 4),
                    "samples": len(rows),
                })
        return trend

    def get_degraded_categories(self, since_hours: int = 168) -> list[str]:
        matrix = self.confusion_matrix(since_hours)
        degraded: list[str] = []
        for true_cat, preds in matrix.items():
            total = sum(preds.values())
            if total < 10:
                continue
            correct = preds.get(true_cat, 0)
            accuracy = correct / total
            if accuracy < 0.7:
                degraded.append(true_cat)
                logger.warning("Category '{}' degraded: accuracy {:.1%} ({} samples)", true_cat, accuracy, total)
        return degraded

    def report(self, since_hours: int = 168) -> dict[str, Any]:
        return {
            "accuracy": self.compute_accuracy(since_hours),
            "category_distribution": self.category_distribution(since_hours),
            "degraded_categories": self.get_degraded_categories(since_hours),
            "period_hours": since_hours,
        }
