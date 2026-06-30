from __future__ import annotations

import pickle
from pathlib import Path

from ai_mini_box_llm.classifier import CATEGORY_CLASSES, ClassifierEnsemble


class TestClassifierEnsemble:
    def test_cold_start_returns_question_zero(self):
        clf = ClassifierEnsemble()
        cat, conf = clf.predict("заказ пиццы")
        assert cat == "ВОПРОС"
        assert conf == 0.0

    def test_fit_and_predict(self):
        clf = ClassifierEnsemble()
        texts = ["заказ пиццы", "сколько стоит", "все сломалось", "давайте работать", "привет"]
        cats = ["ЗАКАЗ", "ВОПРОС", "ЖАЛОБА", "ПРЕДЛОЖЕНИЕ", "ФЛУД"]
        clf.fit_all(texts, cats, [True, False, False, False, False])
        cat, conf = clf.predict("заказ пиццы")
        assert cat in CATEGORY_CLASSES
        assert conf > 0.0

    def test_predict_order(self):
        clf = ClassifierEnsemble()
        texts = ["заказ 2 ноутбука", "спасибо", "хочу купить", "привет"]
        cats = ["ЗАКАЗ", "ФЛУД", "ЗАКАЗ", "ФЛУД"]
        is_order = [True, False, True, False]
        clf.fit_all(texts, cats, is_order)
        order, conf = clf.predict_order("мне нужно 2 ноутбука")
        assert isinstance(order, bool)
        assert 0.0 <= conf <= 1.0

    def test_save_load_consistency(self, tmp_path: Path):
        clf = ClassifierEnsemble()
        texts = ["заказ пиццы", "сколько стоит", "все сломалось"]
        cats = ["ЗАКАЗ", "ВОПРОС", "ЖАЛОБА"]
        clf.fit_all(texts, cats, [True, False, False])
        path = str(tmp_path / "model.pkl")
        clf.save(path)
        cat_before, conf_before = clf.predict("заказ")

        clf2 = ClassifierEnsemble()
        assert clf2.load(path)
        cat_after, conf_after = clf2.predict("заказ")
        assert cat_before == cat_after

    def test_load_returns_false_on_missing(self):
        clf = ClassifierEnsemble()
        assert not clf.load("/nonexistent/path.pkl")

    def test_partial_fit_batch(self):
        clf = ClassifierEnsemble()
        clf.partial_fit_batch(["заказ", "спасибо"], ["ЗАКАЗ", "ФЛУД"])
        assert clf._fitted

    def test_partial_fit_empty_does_nothing(self):
        clf = ClassifierEnsemble()
        clf.partial_fit_batch([], [])
        assert not clf._fitted

    def test_empty_text_returns_question_zero(self):
        clf = ClassifierEnsemble()
        clf.fit_all(["test", "order"], ["ВОПРОС", "ЗАКАЗ"], [False, True])
        cat, conf = clf.predict("")
        assert cat == "ВОПРОС"
        assert conf == 0.0

    def test_predict_folder(self):
        clf = ClassifierEnsemble()
        texts = ["вопрос по цене", "хочу заказать", "проблема с товаром"]
        cats = ["Цены", "Заказ", "Жалоба"]
        clf.fit_all(texts, cats, [False, True, False], folder_labels=["Цены", "Заказ", "Жалоба"])
        result = clf.predict_folder("сколько стоит?", ["Цены", "Заказ", "Жалоба"])
        assert result is None or isinstance(result, str)
