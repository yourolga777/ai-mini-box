from __future__ import annotations

from ai_mini_box_llm.monitoring import DriftMonitor


class _MockTrainingLog:
    def __init__(self, pred, corr):
        self.category_predicted = pred
        self.category_corrected = corr
        self.created_at = None


class _MockSession:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, stmt):
        class _Result:
            def scalars(self):
                return self

            def all(self):
                return [
                    _MockTrainingLog("ЗАКАЗ", "ЗАКАЗ"),
                    _MockTrainingLog("ВОПРОС", "ЗАКАЗ"),
                    _MockTrainingLog("ВОПРОС", "ВОПРОС"),
                ]

            def scalar(self):
                return 3

        return _Result()

    def close(self):
        pass

    def expunge(self, obj):
        pass


class _MockDbFactory:
    def __call__(self):
        return _MockSession()


class TestDriftMonitor:
    def setup_method(self):
        self.monitor = DriftMonitor(_MockDbFactory())

    def test_compute_accuracy(self):
        acc = self.monitor.compute_accuracy()
        assert 0 < acc < 1
        # 2 correct out of 3 = 0.6667

    def test_confusion_matrix(self):
        matrix = self.monitor.confusion_matrix()
        assert "ЗАКАЗ" in matrix

    def test_category_distribution(self):
        dist = self.monitor.category_distribution()
        assert isinstance(dist, dict)

    def test_accuracy_trend(self):
        trend = self.monitor.accuracy_trend(days=3)
        assert isinstance(trend, list)

    def test_report(self):
        report = self.monitor.report()
        assert "accuracy" in report
        assert "category_distribution" in report

    def test_get_degraded_categories(self):
        degraded = self.monitor.get_degraded_categories()
        assert isinstance(degraded, list)
