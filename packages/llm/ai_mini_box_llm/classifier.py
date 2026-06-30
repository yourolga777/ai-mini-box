from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

CATEGORY_CLASSES = ["ЗАКАЗ", "ВОПРОС", "ПРЕДЛОЖЕНИЕ", "ЖАЛОБА", "ФЛУД"]


class ClassifierEnsemble:
    def __init__(self):
        self._vectorizer = HashingVectorizer(
            n_features=2**18,
            analyzer="char_wb",
            ngram_range=(2, 5),
            norm="l2",
            alternate_sign=False,
        )
        self._category_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            warm_start=True,
        )
        self._order_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            warm_start=True,
        )
        self._folder_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            warm_start=True,
        )
        self._category_classes: list[str] = CATEGORY_CLASSES[:]
        self._fitted = False

    def predict(self, text: str) -> tuple[str, float]:
        if not self._fitted or not text.strip():
            return ("ВОПРОС", 0.0)
        X = self._vectorizer.transform([text])
        probs = self._category_clf.predict_proba(X)[0]
        best_idx = int(np.argmax(probs))
        classes = self._category_clf.classes_
        return (str(classes[best_idx]), float(probs[best_idx]))

    def predict_order(self, text: str) -> tuple[bool, float]:
        if not self._fitted or not text.strip():
            return (False, 0.0)
        X = self._vectorizer.transform([text])
        probs = self._order_clf.predict_proba(X)[0]
        classes = self._order_clf.classes_
        if len(classes) < 2:
            return (False, 0.0)
        pos_idx = list(classes).index(True) if True in classes else 0
        return (bool(classes[int(np.argmax(probs))]), float(probs[pos_idx]))

    def predict_folder(self, text: str, folder_names: list[str]) -> str | None:
        if not self._fitted or not text.strip() or not folder_names:
            return None
        X = self._vectorizer.transform([text])
        probs = self._folder_clf.predict_proba(X)[0]
        best_idx = int(np.argmax(probs))
        classes = self._folder_clf.classes_
        return str(classes[best_idx]) if best_idx < len(classes) else None

    def partial_fit_batch(self, texts: list[str], categories: list[str]) -> None:
        if not texts or not categories:
            return
        if len(set(categories)) < 2:
            return
        X = self._vectorizer.transform(texts)
        classes = getattr(self._category_clf, "classes_", None)
        if classes is None or len(classes) == 0:
            classes = self._category_classes
        self._category_clf.partial_fit(X, categories, classes=list(classes))
        self._fitted = True

    def fit_all(
        self,
        texts: list[str],
        categories: list[str],
        is_order: list[bool],
        folder_labels: list[str] | None = None,
    ) -> None:
        if not texts:
            return
        X = self._vectorizer.fit_transform(texts)
        self._category_clf.fit(X, categories)
        self._order_clf.fit(X, is_order)
        if folder_labels:
            self._folder_clf.fit(X, folder_labels)
        self._fitted = True

    def save(self, path: str = "data/classifier_model.pkl") -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "vectorizer": self._vectorizer,
            "category_clf": self._category_clf,
            "order_clf": self._order_clf,
            "folder_clf": self._folder_clf,
            "fitted": self._fitted,
        }
        with open(p, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str = "data/classifier_model.pkl") -> bool:
        p = Path(path)
        if not p.exists():
            return False
        with open(p, "rb") as f:
            data = pickle.load(f)
        self._vectorizer = data["vectorizer"]
        self._category_clf = data["category_clf"]
        self._order_clf = data["order_clf"]
        self._folder_clf = data["folder_clf"]
        self._fitted = data["fitted"]
        return True
