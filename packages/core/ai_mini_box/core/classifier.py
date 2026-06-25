import re
from abc import ABC, abstractmethod

from .models import Topic


class Classifier(ABC):
    @abstractmethod
    def classify(self, text: str) -> Topic:
        ...


class KeywordClassifier(Classifier):
    _RULES: list[tuple[re.Pattern, Topic]] = [
        (re.compile(r"(цена|стоит|руб|доллар|евро|скидк|акци|оплат|сколько)", re.I), Topic.PRICES),
        (re.compile(r"(заказ|купи|закаж|оформи|достав|товар|позици)", re.I), Topic.ORDER),
        (re.compile(r"(жалоб|проблем|не работ|ошибк|плох|возврат|брак)", re.I), Topic.COMPLAINT),
        (re.compile(r"(график|врем|час|расписан|когда|открыт|закрыт)", re.I), Topic.SCHEDULE),
    ]

    def classify(self, text: str) -> Topic:
        for pattern, topic in self._RULES:
            if pattern.search(text):
                return topic
        return Topic.OTHER


_LLM_AVAILABLE = False
try:
    import llama_cpp  # noqa: F401

    _LLM_AVAILABLE = True
except ImportError:
    pass


def create_classifier() -> Classifier:
    if _LLM_AVAILABLE:
        from .classifier_llm import LlmCppClassifier

        try:
            return LlmCppClassifier()
        except Exception:
            pass
    return KeywordClassifier()
