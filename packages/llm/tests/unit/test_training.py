from __future__ import annotations

from ai_mini_box_llm.classifier import ClassifierEnsemble
from ai_mini_box_llm.training import Trainer


class _MockSession:
    def __init__(self):
        self.added = []
        self.flushed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True

    def execute(self, stmt):
        class _Result:
            def scalar(self):
                return 0

            def scalars(self):
                return self

            def all(self):
                return []

        return _Result()

    def close(self):
        pass

    def expunge(self, obj):
        pass


class _MockDbFactory:
    def __call__(self):
        return _MockSession()


class TestTrainer:
    def setup_method(self):
        self.classifier = ClassifierEnsemble()
        self.classifier.fit_all(
            ["заказ пиццы", "сколько стоит", "все сломалось", "давайте работать", "привет"],
            ["ЗАКАЗ", "ВОПРОС", "ЖАЛОБА", "ПРЕДЛОЖЕНИЕ", "ФЛУД"],
            [True, False, False, False, False],
        )
        self.trainer = Trainer(self.classifier, _MockDbFactory())

    def test_log_correction(self):
        session = _MockDbFactory()()
        self.trainer._db = lambda: session
        self.trainer.log_correction(
            message_text="тест",
            category_corrected="ВОПРОС",
            category_predicted="ФЛУД",
        )
        assert len(session.added) == 1
        assert session.flushed

    def test_collect_batch_empty(self):
        texts, cats = self.trainer.collect_batch(min_samples=50)
        assert texts == []
        assert cats == []

    def test_train_on_batch(self):
        texts = ["заказ", "сколько"]
        cats = ["ЗАКАЗ", "ВОПРОС"]
        result = self.trainer.train_on_batch(texts, cats)
        assert "accuracy" in result
        assert result["trained"] is True

    def test_train_on_empty(self):
        result = self.trainer.train_on_batch([], [])
        assert result["trained"] is False

    def test_auto_train_no_data(self):
        result = self.trainer.auto_train()
        assert result["trained"] is False
