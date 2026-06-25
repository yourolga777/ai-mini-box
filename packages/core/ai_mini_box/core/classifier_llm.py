from pathlib import Path

from loguru import logger

from ai_mini_box.infrastructure.config import JsonConfigManager

from .classifier import Classifier
from .models import Topic

_PROMPT = """Classify the message into one of these categories:
- PRICES (Цены) — questions about price, cost, discounts
- ORDER (Заказ) — orders, purchases, delivery
- COMPLAINT (Жалоба) — complaints, problems, returns
- SCHEDULE (График) — working hours, schedule, timing
- OTHER (Другое) — everything else

Message: {text}
Category:"""


class LlmCppClassifier(Classifier):
    def __init__(self):
        self._model = None
        try:
            import llama_cpp  # noqa: F401

            config = JsonConfigManager().load()
            model_path = Path(config.llm_model_path)
            if not model_path.exists():
                logger.warning("LLM model not found at {}", model_path)
                raise FileNotFoundError(str(model_path))

            self._model = llama_cpp.Llama(
                model_path=str(model_path),
                n_ctx=config.llm_n_ctx,
                n_threads=config.llm_n_threads,
                verbose=False,
            )
            logger.info("Loaded LLM model from {}", model_path)
        except Exception as e:
            logger.warning("Failed to initialize LlmCppClassifier: {}", e)
            raise

    def classify(self, text: str) -> Topic:
        if self._model is None:
            return Topic.OTHER
        try:
            output = self._model(
                _PROMPT.format(text=text),
                max_tokens=10,
                temperature=0.0,
                stop=["\n"],
            )
            label = output["choices"][0]["text"].strip().upper()
            return Topic(label) if label in Topic._value2member_map_ else Topic.OTHER
        except Exception as e:
            logger.warning("LLM classification failed: {}", e)
            return Topic.OTHER
