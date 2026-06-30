# Спецификация: LLM Rewrite + 3-слойная система шаблонов (Архитектурный обзор)

**Разработчик:** core-developer / web-developer / llm-developer  
**Приоритет:** P0  
**Статус:** **SUPERSEDED** — разделена на три отдельных spec по ролям:
- [27-llm-core-rewrite.md](27-llm-core-rewrite.md) — ML-ядро + Template Engine (llm-dev)
- [25-web-templates-spec.md](25-web-templates-spec.md) — REST API + React UI (web-dev)
- [26-telegram-pipeline-spec.md](26-telegram-pipeline-spec.md) — Telegram handler (telegram-dev)

Данный документ оставлен как архитектурный обзор системы.  
Детали реализации смотрите в соответствующих spec выше.

---

## Часть A: Переписывание LLM-плагина

### A0. Мотивация и цели

Существующий LLM-плагин использует `llama-cpp-python` + GGUF-модель для всех задач:
классификации, экстракции сущностей, генерации ответов. Это даёт:

| Проблема | Влияние |
|---|---|
| RAM 2-4 ГБ на инференс | Не помещается на малых серверах |
| 5-30 секунд на сообщение | UX убит, операторы ждут |
| Нет обучения | Каждое исправление оператора теряется |
| `llama-cpp-python` — тяжёлая C++ зависимость | Проблемы с установкой, сборкой |

**Новая архитектура:** HashingVectorizer + SGDClassifier (онлайн-обучение batch-ами),
regex-экстракция, FAISS + all-MiniLM-L6-v2 для RAG, LRU-кэш, pipeline-оркестратор.

---

### A1. Pipeline (новый файл)

**Файл:** `packages/llm/ai_mini_box_llm/pipeline.py` (новый)

**Описание:** Центральный оркестратор обработки сообщения. Заменяет `ChatbotService`
и прямое использование провайдеров.

**ProcessingContext:**
```python
@dataclass
class ProcessingContext:
    text: str
    history: list[dict] = field(default_factory=list)
    user_name: str = ""
    category: str | None = None
    contact_id: int | None = None
    business_config: dict | None = None
```

```python
class Pipeline:
    """
    Сквозная обработка входящего сообщения.
    """
    def __init__(
        self,
        classifier: ClassifierEnsemble,
        entity_extractor: EntityExtractor,
        template_selector: TemplateSelector,
        rag: Retriever,
        cache: ResponseCache,
    ):
        ...

    def process(self, text: str, context: ProcessingContext) -> PipelineResult:
        """Обработать сообщение: кэш → препроцессинг → классификация → экстракция → RAG → шаблон"""
```

**Порядок шагов:**

```
1. КЭШ (LRU, TTL=7d):      хеш(text) → готовый PipelineResult
                              │ hit → return
                              │ miss → дальше
                              ▼
2. ПРЕПРОЦЕССИНГ:           очистка (эмодзи, повторы, нормализация "прив"→"привет")
                              ▼
3. КЛАССИФИКАЦИЯ:           HashingVectorizer + SGD → (category, confidence)
                              если confidence < 0.6 → need_human = true
                              ▼
4. ЭКСТРАКЦИЯ СУЩНОСТЕЙ:    regex → phone, date, time, address, name
                              ▼
5. RAG (FAISS + MiniLM):    поиск по истории успешных ответов
                              если top1.confidence > 0.75 → используем ответ
                              ▼
6. ВЫБОР ШАБЛОНА:           system > business > learned > fallback
                              ▼
7. ЗАПОЛНЕНИЕ ПЕРЕМЕННЫХ:   подстановка {{name}}, {{order}} и т.д.
                              ▼
8. КЭШИРОВАНИЕ РЕЗУЛЬТАТА:  сохраняем в LRU-кэш
                              ▼
9. ВОЗВРАТ PipelineResult
```

**PipelineResult:**

```python
@dataclass
class PipelineResult:
    category: str                         # ЗАКАЗ | ВОПРОС | ПРЕДЛОЖЕНИЕ | ЖАЛОБА | ФЛУД
    confidence: float                     # 0.0–1.0
    need_human: bool
    reply_text: str | None               # готовый ответ (если есть)
    reply_source: str                    # "cache" | "rag" | "template" | "fallback"
    entities: dict[str, Any]             # извлечённые сущности
    is_order: bool
    template_id: str | None              # ID использованного шаблона
    processing_time_ms: int
```

**Критерии приёмки:**
- Весь pipeline проходит за < 50 ms (с кэшем < 1 ms)
- При confidence < 0.6 → `need_human = true`, fallback-ответ
- При пустом тексте → возврат без ошибки
- Все шаги обработаны в try/except — pipeline не падает

---

### A2. Классификатор (HashingVectorizer + SGD)

**Файл:** `packages/llm/ai_mini_box_llm/classifier.py` (новый)

**Описание:** Ensemble из 3 классификаторов на одной векторной основе:
1. **5-категорийный** (ЗАКАЗ/ВОПРОС/ПРЕДЛОЖЕНИЕ/ЖАЛОБА/ФЛУД)
2. **Бинарный** (заказ/не заказ)
3. **Folder-классификатор** (категория → папка)

```python
class ClassifierEnsemble:
    def __init__(self):
        # Единый на всю систему HashingVectorizer
        self._vectorizer = HashingVectorizer(
            n_features=2**18,          # 262k features
            analyzer="char_wb",        # символьные n-граммы — лучше для чата
            ngram_range=(2, 5),        # 2-5 символьных групп
            norm="l2",
            alternate_sign=False,      # стабильность признаков
        )
        # Три независимых классификатора
        self._category_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            class_weight="balanced",
            warm_start=True,           # для batch re-fit
        )
        self._order_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            class_weight="balanced",
            warm_start=True,
        )
        self._folder_clf = SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            class_weight="balanced",
            warm_start=True,
        )

        # Словарь классов — фиксируется при первом fit
        self._category_classes: list[str] = []
        self._fitted = False

    def predict(self, text: str) -> tuple[str, float]:
        """Возвращает: (category, confidence)"""

    def predict_order(self, text: str) -> tuple[bool, float]:
        """Возвращает: (is_order, confidence)"""

    def predict_folder(self, text: str, folder_names: list[str]) -> str | None:
        """Возвращает название папки или None"""

    def partial_fit_batch(self, texts: list[str], categories: list[str]):
        """Batch re-fit на новых данных (раз в час или по накоплению 50+ записей)"""
        X = self._vectorizer.transform(texts)
        self._category_clf.partial_fit(X, categories, classes=self._category_classes)
        self._fitted = True

    def fit_all(
        self,
        texts: list[str],
        categories: list[str],
        is_order: list[bool],
        folder_labels: list[str] | None = None,
    ):
        """Полное переобучение с нуля (ночной retrain)"""
```

**Загрузка/сохранение:**
```python
def save(self, path: str = "data/classifier_model.pkl"):
    """Сохраняет векторизатор + веса всех 3 классификаторов"""

def load(self, path: str = "data/classifier_model.pkl") -> bool:
    """Загружает. Возвращает False, если файла нет (холодный старт)."""
```

**Холодный старт:** Начальный датасет генерируется скриптом `scripts/generate_synthetic.py`
(см. A8). Без него классификатор возвращает `("ВОПРОС", 0.0)` — все сообщения
на оператора, пока не накопится 200+ реальных размеченных.

**Критерии приёмки:**
- `predict("заказ пиццы")` → `("ЗАКАЗ", > 0.6)`
- `predict("когда приедет")` → `("ВОПРОС", > 0.6)`
- `predict_order("мне нужно 2 ноутбука")` → `(True, > 0.7)`
- `predict_order("спасибо")` → `(False, > 0.9)`
- Batch fit не падает при 1 записи (граничный случай)
- Сохранение/загрузка работает: save → load → predict без расхождений

---

### A3. Экстрактор сущностей (regex-based)

**Файл:** `packages/llm/ai_mini_box_llm/extractor.py` (новый)

**Описание:** Извлечение сущностей из текста без ML. Только regex + простые
эвристики. Заменяет `extract_entities()` и `extract_order_info()` из старого
провайдера.

```python
class EntityExtractor:
    PHONE_RE = re.compile(r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}")
    DATE_RE = re.compile(
        r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?"       # 15.06.2026, 15/06
        r"|(завтра|сегодня|послезавтра|через\s+\d+\s+(день|дня|дней|недел[юяи]|месяц[а]?))"
    )
    TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(?:утра|дня|вечера)?")
    ADDRESS_RE = re.compile(
        r"(?:ул\.?|улица|пр\.?|проспект|д\.?|дом|кв\.?|квартира)\s*[а-яА-Я0-9\s.-]+"
    )
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    NAME_RE = re.compile(
        r"(?:меня\s+зовут|я\s+[\w]+|клиент|покупател[ья])\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)"
    )

    # Нормализация сообщений
    NORMALIZE_MAP = {
        "прив": "привет",
        "здрасте": "здравствуйте",
        "спс": "спасибо",
        "щас": "сейчас",
        "мб": "может быть",
        "пж": "пожалуйста",
        "плз": "пожалуйста",
        "норм": "нормально",
        "ок": "хорошо",
    }

    def normalize(self, text: str) -> str:
        """Нормализация сленга, эмодзи, повторов"""

    def extract(self, text: str) -> dict[str, Any]:
        """Извлекает: phone, email, date, time, address, name"""

    def extract_order_items(self, text: str) -> list[dict]:
        """
        Парсинг товаров в заказе.
        Возвращает список: [{"product": "Ноутбук", "quantity": 2, "price": 15000}]
        """

    def has_product_keywords(self, text: str) -> bool:
        """Проверяет наличие ключевых слов заказа (купить, заказать, нужно N шт.)"""
```

**Критерии приёмки:**
- `extract("+7 999 123-45-67")` → `{"phone": "+7 999 123-45-67"}`
- `extract("завтра в 15:00")` → `{"date": "2026-06-30", "time": "15:00"}`
- `extract("меня зовут Иван Петров")` → `{"name": "Иван Петров"}`
- `extract("норм, спс")` → `{}` (нормализовано, но сущностей нет)
- `extract("")` → `{}`
- `extract_order_items("2 ноутбука Lenovo")` → `[{"product": "ноутбук Lenovo", "quantity": 2}]`
- Регекспы не падают на None/пустой строке

---

### A4. RAG (FAISS + all-MiniLM-L6-v2 via ONNX)

**Файлы:**
- `packages/llm/ai_mini_box_llm/rag/embeddings.py` (переписать)
- `packages/llm/ai_mini_box_llm/rag/vector_store.py` (переписать)
- `packages/llm/ai_mini_box_llm/rag/retriever.py` (переписать)

**Описание:** Замена JSON-based векторного хранилища на FAISS.
Embeddings через `onnxruntime` + `all-MiniLM-L6-v2` (384 dim, ~80 МБ RAM).
Модель авто-загружается при первом вызове `EmbeddingModel()` — без отдельной CLI.

```python
class EmbeddingModel:
    ONNX_MODEL_URL = "https://huggingface.co/optimum/all-MiniLM-L6-v2/resolve/main/model.onnx"
    LOCAL_PATH = "data/embeddings/model.onnx"

    def __init__(self):
        self._session = None
        self._load()

    def _load(self):
        """Авто-загрузка ONNX модели при первом вызове."""
        import onnxruntime
        from pathlib import Path
        path = Path(self.LOCAL_PATH)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            # скачиваем из предустановленного репозитория или bundled asset
            self._download_model()
        self._session = onnxruntime.InferenceSession(str(path))

    def embed(self, text: str) -> list[float]:
        """384-dim вектор"""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch-embeddings (оптимизировано)"""

class FaissVectorStore:
    def __init__(self, dim: int = 384, index_path: str = "data/rag_index.faiss"):
        self._index = faiss.IndexFlatIP(dim)  # Inner Product = cosine on normalized
        self._metadata: list[dict] = []
        self._index_path = Path(index_path)

    def add(self, text: str, embedding: list[float], metadata: dict):
        ...

    def search(self, query_vec: list[float], top_k: int = 3, threshold: float = 0.75
    ) -> list[tuple[str, float, dict]]:
        """Возвращает: [(text, score, metadata), ...]"""

    def save(self):
        """Сохраняет FAISS index + metadata JSON"""

    def load(self) -> bool:
        """Загружает. Возвращает False если файла нет."""

class Retriever:
    def __init__(self, embed_model: EmbeddingModel, store: FaissVectorStore):
        ...

    def retrieve(self, text: str, top_k: int = 3) -> list[tuple[str, float, dict]]:
        """Получить релевантные ответы из RAG"""

    def add_successful_reply(self, question: str, answer: str, category: str):
        """Добавить успешный ответ оператора в RAG-индекс"""

    def rebuild_index(self, texts: list[str], metadatas: list[dict]):
        """Полная перестройка индекса (ночной retrain)"""
```

**Критерии приёмки:**
- Размер index в RAM: < 50 МБ на 10k записей
- Поиск: < 10 ms на 10k записей (FAISS IVF или Flat)
- threshold=0.75 отсекает нерелевантные результаты
- Rebuild индекса не блокирует чтение (copy-on-write через временный файл)
- Если модель не загрузилась (нет `onnxruntime` или не скачалась) → RAG отключён, лог WARNING

---

### A5. Кэш ответов

**Файл:** `packages/llm/ai_mini_box_llm/cache.py` (новый)

```python
class ResponseCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 604800):  # 7 days
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, text: str) -> PipelineResult | None:
        """Хеш текста → результат. None если нет или TTL истёк."""

    def set(self, text: str, result: PipelineResult):
        """Сохранить результат в кэш."""

    def invalidate(self, template_id: str):
        """Сбросить кэш для сообщений, использующих конкретный шаблон."""

    def stats(self) -> dict:
        """hit_count, miss_count, size, oldest_entry_age"""
```

**Критерии приёмки:**
- 80% повторяющихся сообщений (здравствуйте, спасибо) — hit из кэша
- TTL 7 дней — через неделю кэш устаревает
- При изменении шаблона → `invalidate(template_id)` сбрасывает зависимые записи
- При достижении maxsize вытесняется LRU-запись

---

### A6. Обучение (batch)

**Файл:** `packages/llm/ai_mini_box_llm/training.py` (новый)

```python
class TrainingLog(Base):
    """Хранилище действий оператора для batch-обучения"""
    __tablename__ = "training_log"
    id: int (PK, autoincrement)
    message_text: str
    category_predicted: str | None       # что предсказала система
    category_corrected: str | None       # что исправил оператор
    is_order_predicted: bool | None
    is_order_corrected: bool | None
    template_id_used: int | None         # какой шаблон был использован
    operator_approved: bool | None       # оператор одобрил ответ
    operator_edited: bool | None         # оператор правил ответ
    final_reply_text: str | None         # что реально ушло клиенту
    created_at: datetime (default=now)

class Trainer:
    """
    Batch-обучение классификаторов.
    Не partial_fit после каждого исправления — накопление и переобучение.
    """
    def __init__(self, classifier: ClassifierEnsemble, db_session_factory):
        ...

    def log_correction(self, message_text: str, category_corrected: str,
                       category_predicted: str | None = None):
        """Сохранить исправление оператора в TrainingLog"""

    def collect_batch(self, min_samples: int = 50) -> tuple[list[str], list[str]]:
        """Собрать батч из TrainingLog с минимумом min_samples записей"""

    def train_on_batch(self, texts: list[str], categories: list[str]) -> dict:
        """Переобучить классификатор. Возвращает метрики."""

    def auto_train(self):
        """Проверить, хватит ли данных, и если да — переобучить."""

    def nightly_retrain(self):
        """Полное переобучение с нуля (ночной retrain по расписанию)."""
```

**Расписание обучения:**

| Тип | Триггер | Действие |
|---|---|---|
| Batch fit | Каждые 50 новых записей в TrainingLog | `partial_fit` с накопленным батчем |
| Nightly retrain | 03:00 по серверу | Полный fit с нуля на всех данных за 30 дней |
| On-demand | Через CLI/API | `trainer.auto_train()` |

**Критерии приёмки:**
- При 0 записях в TrainingLog — `auto_train()` не делает ничего
- `train_on_batch()` возвращает accuracy на тестовой выборке (20% от батча)
- Nightly retrain не блокирует текущие запросы (сначала `fit`, потом swap)
- Старая модель сохраняется как backup перед переобучением

---

### A7. Мониторинг дрейфа

**Файл:** `packages/llm/ai_mini_box_llm/monitoring.py` (новый)

```python
class DriftMonitor:
    """
    Отслеживание качества классификатора.
    """

    def compute_accuracy(self, since_hours: int = 168) -> float:
        """Accuracy на TrainingLog за N часов (по умолч. неделя)"""

    def confusion_matrix(self, since_hours: int = 168) -> dict:
        """Матрица ошибок по категориям"""

    def category_distribution(self, since_hours: int = 168) -> dict[str, int]:
        """Распределение категорий за период"""

    def accuracy_trend(self, days: int = 30) -> list[dict]:
        """Тренд accuracy по дням"""

    def get_degraded_categories(self) -> list[str]:
        """Категории с accuracy < 70% — нужно переобучение или новые данные"""

    def report(self) -> dict:
        """Сводный отчёт для дашборда"""
```

**Критерии приёмки:**
- `compute_accuracy()` — корректное отношение правильных/всех исправлений
- При accuracy < 70% — запись в лог уровня WARNING
- `get_degraded_categories()` — только для категорий с > 10 исправлений за период

---

### A8. Генерация синтетических данных (холодный старт)

**Файл:** `packages/llm/ai_mini_box_llm/scripts/generate_synthetic.py` (новый)

**Описание:** Генерация 500-1000 сообщений на каждую категорию для первичного
обучения классификатора.

```python
def generate_synthetic_dataset() -> list[tuple[str, str, bool]]:
    """
    Возвращает: [(text, category, is_order), ...]
    Категории: ЗАКАЗ, ВОПРОС, ЖАЛОБА, ПРЕДЛОЖЕНИЕ, ФЛУД
    """
    # Использует шаблоны + рандомизацию (не внешний LLM)
    # Примеры:
    # - "Здравствуйте! Хочу заказать {product} в количестве {n} штук" → ЗАКАЗ, is_order=True
    # - "Сколько стоит {product}?" → ВОПРОС, is_order=False
    # - "У меня сломался {product}, хочу вернуть" → ЖАЛОБА, is_order=False
```

**CLI-команда:** `ai-mini-box llm generate-synthetic [--count 500]`

**Результат:** JSON-файл `data/synthetic_dataset.json` + immediate `fit_all()`

**Критерии приёмки:**
- После генерации классификатор предсказывает с accuracy > 70% на тестовых данных
- Каждая категория представлена минимум 200 сообщениями
- Сообщения на русском, в разговорном стиле
- Нет дубликатов

---

### A9. Интеграция в plugin.py

**Файл:** `packages/llm/ai_mini_box_llm/plugin.py` (изменения)

**Что меняется:**

```python
def register(app: typer.Typer) -> None:
    _ensure_tables()
    _seed_system_categories()

    try:
        # 1. Загружаем или создаём классификатор
        classifier = ClassifierEnsemble()
        if not classifier.load():
            logger.info("No pre-trained classifier found — generating synthetic data")
            from .scripts.generate_synthetic import generate_and_train
            generate_and_train(classifier)

        # 2. Entity extractor
        extractor = EntityExtractor()

        # 3. Embedding model + FAISS
        embed_model = EmbeddingModel()
        vector_store = FaissVectorStore()
        retriever = Retriever(embed_model, vector_store)

        # 4. Template store
        template_store = TemplateStore(...)
        SystemTemplateSync(db_session).sync_on_startup()

        # 5. Cache
        cache = ResponseCache()

        # 6. Template selector (см. Часть B)
        template_selector = TemplateSelector(template_store, retriever)

        # 7. Pipeline
        pipeline = Pipeline(classifier, extractor, template_selector, retriever, cache)

        # 8. Trainer
        trainer = Trainer(classifier, get_db)
        register_service("trainer", trainer)

        # 9. Drift monitor
        monitor = DriftMonitor()
        register_service("drift_monitor", monitor)

        # 10. Регистрируем pipeline как основную LLM-службу
        register_service("llm", pipeline)  # заменяет старый LlmServiceImpl
        logger.info("LLM pipeline registered")

    except Exception as e:
        logger.warning("LLM plugin initialization failed: {}", e)
```

**CLI-команды — остаются** (status, classify, draft, extract),
но их реализация меняется на использование pipeline.
`download-model` **удалён** — RAG-модель авто-загружается при инициализации EmbeddingModel.

**Добавить CLI-команды:**
```python
@llm_app.command()
def retrain():
    """Ручное переобучение классификатора."""
    trainer = get_service("trainer")
    metrics = trainer.auto_train()
    typer.echo(f"Retrained. Accuracy: {metrics['accuracy']:.1%}")

@llm_app.command()
def generate_synthetic(count: int = 500):
    """Сгенерировать синтетические данные для холодного старта."""

@llm_app.command()
def accuracy():
    """Показать accuracy классификатора за неделю."""
```

**pyproject.toml — зависимости:**
```toml
# Удалить:
# [project.optional-dependencies]
# local = ["llama-cpp-python>=0.2"]
# download = ["huggingface-hub>=0.20"]

# Добавить:
dependencies = [
    "ai-mini-box-core>=5.0.0",
    "scikit-learn>=1.3",
    "onnxruntime>=1.15",
    "faiss-cpu>=1.7",
]

[project.optional-dependencies]
remote = ["openai>=1.0"]          # оставляем для удалённого провайдера
dev = ["pytest>=8"]
```

**Удалить целиком:**
- `packages/llm/ai_mini_box_llm/providers/` (local.py, remote.py, base.py)
- `packages/llm/ai_mini_box_llm/chatbot_service.py`
- `packages/llm/ai_mini_box_llm/prompt.py`

---

### A10. Web API endpoints (обновление)

**Файл:** `packages/web/ai_mini_box_web/routers/messages.py` (изменения)

**Что меняется:** эндпоинт `POST /api/messages/{id}/reprocess-chatbot` теперь
использует pipeline вместо chatbot_service.

```python
@router.post("/{item_id}/reprocess-chatbot")
def reprocess_message_chatbot(item_id: int, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404)

    pipeline = get_service("llm")  # Pipeline, не ChatbotService
    if pipeline is None:
        raise HTTPException(400, detail="LLM pipeline not available")

    result = pipeline.process(msg.text, ProcessingContext(
        history=[],
        user_name=msg.extracted_name or "",
        category=msg.category,
    ))

    # Сохраняем результат
    msg.category = result.category
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"
    repos.messages.update(msg)

    return {
        "success": True,
        "category": result.category,
        "reply_to_user": result.reply_text,
        "need_human": result.need_human,
        "auto_replied": msg.auto_replied,
    }
```

---

### A11. Telegram handler (обновление)

**Файл:** `packages/telegram/ai_mini_box_telegram/handlers.py` (изменения)

```python
def process_update(update: dict, session, allowed_chat_ids=None) -> bool:
    # ... (сохранение message как и раньше) ...

    pipeline = get_service("llm")
    if pipeline is None:
        logger.warning("LLM pipeline not available, skipping")
        return True

    try:
        history = get_chat_history(repos, str(chat_id))
        result = pipeline.process(text, ProcessingContext(
            history=history,
            user_name=user_name,
            category=None,
        ))
    except Exception:
        logger.exception("Pipeline processing failed")
        return True

    msg.category = result.category
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"

    repos.messages.update(msg)

    # Автоответ, если нужно
    if msg.auto_replied and result.reply_text:
        tg = get_service("telegram")
        if tg:
            tg.send_message(chat_id, result.reply_text)
            msg.sent_response = True
            repos.messages.update(msg)

    return True
```

---

### A12. AutoProcessor (обновление)

**Файл:** `packages/llm/ai_mini_box_llm/auto_processor.py` (изменения)

```python
class AutoProcessor:
    def process(self, message: Message, contact: Contact) -> AutoProcessResult:
        result = AutoProcessResult()
        repos = self._get_repos()

        pipeline = get_service("llm")
        if pipeline is None or not message.text:
            return result

        p_result = pipeline.process(message.text, ProcessingContext(
            history=[], user_name=message.extracted_name or "", category=None
        ))

        # Извлечённые сущности → обновление контакта
        if p_result.entities.get("phone") and contact:
            # обновление телефона
            pass

        # Создание заказа, если is_order
        if p_result.is_order:
            order = Order(
                contact_id=message.contact_id,
                source_message_id=message.id,
                notes=message.text,
                status="new",
            )
            created = repos.orders.add(order)
            message.extracted_order_id = created.id
            repos.messages.update(message)
            result.order_created = True

        # Назначение папки
        folder_id = self._assign_llm_folder(repos, message, p_result.category)
        if folder_id:
            result.folder_assigned = True

        return result
```

---

## Часть B: 3-слойная система шаблонов

### B0. Мотивация и цели

Система шаблонов заменяет генеративную LLM для ответов клиентам.
Используется, когда RAG не нашёл подходящего ответа, или когда
нужен гарантированный формат ответа.

**3 слоя:**
1. **System** — юридические, неизменяемые (из `business_config.json`)
2. **Business** — редактируемые через UI (оператор/менеджер)
3. **Learned (RAG)** — автоматически извлечённые из успешных ответов

---

### B1. Модели данных (SQLite — единый движок с core)

**Файл:** `packages/llm/ai_mini_box_llm/models.py` (добавить)

**Решение:** SQLite. UUID как hex-строка (`uuid.uuid4().hex`), JSON как TEXT
с Pydantic-валидацией через property, BOOLEAN как INTEGER (0/1).
Миграция на PostgreSQL — смена драйвера + DATABASE_URL без переписывания кода.

```sql
CREATE TABLE templates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    scope TEXT NOT NULL CHECK (scope IN ('system', 'business', 'learned')),
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    text TEXT NOT NULL,
    variables TEXT DEFAULT '[]',
    defaults TEXT DEFAULT '{}',
    triggers TEXT DEFAULT '[]',
    confidence_min REAL DEFAULT 0.6,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    is_archived INTEGER DEFAULT 0,
    created_by_id TEXT,
    updated_by_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scope, slug)
);

CREATE INDEX idx_templates_scope_category_active
    ON templates(scope, category, is_active)
    WHERE is_active = 1 AND is_archived = 0;

CREATE TABLE template_usage_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    template_id TEXT NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    message_id TEXT,
    category TEXT,
    confidence REAL,
    was_used INTEGER DEFAULT 1,
    operator_approved INTEGER,
    operator_edited INTEGER DEFAULT 0,
    final_text TEXT,
    response_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_log_template_id ON template_usage_log(template_id);
CREATE INDEX idx_usage_log_created_at ON template_usage_log(created_at DESC);
```

**SQLAlchemy модель (ключевые моменты):**

```python
class Template(Base):
    __tablename__ = "templates"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    scope = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    # JSON как TEXT с validation через property
    _variables = Column("variables", Text, default="[]")
    _defaults = Column("defaults", Text, default="{}")
    _triggers = Column("triggers", Text, default="[]")
    confidence_min = Column(Float, default=0.6)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    is_archived = Column(Integer, default=0)
    created_by_id = Column(String(32), nullable=True)
    updated_by_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("scope", "slug", name="uq_templates_scope_slug"),
    )

    @property
    def variables(self) -> list[str]:
        try: return json.loads(self._variables)
        except: return []

    @variables.setter
    def variables(self, value: list[str]):
        self._variables = json.dumps(value, ensure_ascii=False)

    # defaults, triggers — аналогично

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return round((self.success_count / self.usage_count) * 100, 1)

class TemplateUsageLog(Base):
    __tablename__ = "template_usage_log"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    template_id = Column(String(32), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(32), nullable=True)
    category = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    was_used = Column(Integer, default=1)
    operator_approved = Column(Integer, nullable=True)
    operator_edited = Column(Integer, default=0)
    final_text = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

---

### B2. Хранилище шаблонов

**Файл:** `packages/llm/ai_mini_box_llm/templates/store.py` (новый)

```python
class TemplateStore:
    """
    Единая точка доступа к шаблонам из всех трёх слоёв.
    """
    def __init__(self, db_session_factory):
        self._db = db_session_factory

    # CRUD
    def get(self, template_id: str) -> Template | None: ...
    def list(self, scope: str | None = None, category: str | None = None,
             is_active: bool = True) -> list[Template]: ...
    def create(self, data: TemplateCreate) -> Template: ...
    def update(self, template_id: str, data: TemplateUpdate) -> Template: ...
    def delete(self, template_id: str, hard: bool = False): ...

    # Selection logic
    def find_best(self, category: str, text: str, confidence: float
                  ) -> Template | None:
        """Поиск подходящего шаблона: слой 1 → 2 → fallback"""

    def find_by_triggers(self, text: str) -> Template | None:
        """Поиск по ключевым словам (для слоя 1 — system)"""

    def find_by_category(self, category: str, confidence: float) -> Template | None:
        """Поиск среди business-шаблонов по категории, сортировка по success_rate"""

    def increment_usage(self, template_id: str, approved: bool | None = None): ...
```

### B3. System template sync

**Файл:** `packages/llm/ai_mini_box_llm/templates/sync.py` (новый)

```python
class SystemTemplateSync:
    """
    Синхронизация system-шаблонов из business_config.json в БД.
    Вызывается при старте приложения.
    """

    def sync_on_startup(self):
        """
        1. Загрузить system templates из business_config.json
        2. Для каждого: если нет в БД → создать
           если есть, но текст изменился → обновить (version+1)
           если удалён из конфига → is_archived=True
        3. Никогда не удаляет из БД — только архивирует
        """
```

**Формат в `business_config.json`:**
```json
{
  "templates": {
    "system": {
      "legal_disclaimer": {
        "text": "Для расторжения договора обратитесь в офис с паспортом.",
        "category": "complaint",
        "triggers": ["расторг", "отказ", "закрыть счёт"],
        "immutable": true
      },
      "offline_hours": {
        "text": "Сейчас нерабочее время. Мы ответим завтра с 9:00.",
        "category": "question",
        "schedule": "20:00-09:00",
        "immutable": true
      }
    }
  }
}
```

---

### B4. Выбор шаблона (runtime)

**Файл:** `packages/llm/ai_mini_box_llm/templates/store.py` (метод `find_best`)

**Алгоритм:**
```
1. Проверить system-триггеры (по ключевым словам в тексте)
   Если найден → использовать (юридическая безопасность)
2. Найти business-шаблон:
   a. Отфильтровать по category
   b. confidence >= confidence_min
   c. Отсортировать по success_rate DESC
   d. Взять первый, где все переменные есть в entities
3. Попробовать RAG (learned):
   a. similarity > 0.75 → использовать
4. Fallback:
   a. Общий шаблон "Ожидайте ответа"
   b. Если и его нет → "Здравствуйте! Я передал ваш запрос специалисту."
```

```python
def find_best(self, category: str, text: str, entities: dict[str, Any],
              confidence: float, rag_result: RAGResult | None = None) -> Template | None:
    # 1. System triggers
    system_t = self.find_by_triggers(text)
    if system_t:
        return system_t

    # 2. Business templates
    business = self.find_by_category(category, confidence)
    if business:
        return business

    # 3. RAG
    if rag_result and rag_result.score > 0.75:
        return Template(
            scope="learned",
            text=rag_result.text,
            variables=list(entities.keys()),
        )

    # 4. Fallback
    return self._get_fallback()
```

---

### B5. API endpoints (REST)

**Файл:** `packages/web/ai_mini_box_web/routers/templates.py` (новый, web-пакет)
Router импортирует `TemplateStore` из `ai_mini_box_llm.templates.store`.

```python
router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# --- CRUD ---
@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    scope: str | None = None, category: str | None = None,
    is_active: bool | None = None, search: str | None = None,
    limit: int = 50, offset: int = 0,
): ...

@router.post("/", response_model=TemplateResponse)
async def create_template(data: TemplateCreate): ...

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str): ...

@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, data: TemplateUpdate): ...

@router.delete("/{template_id}")
async def delete_template(template_id: str, hard: bool = False): ...

# --- Selection & Usage ---
@router.get("/suggest")
async def suggest_templates(
    message: str, category: str | None = None, limit: int = 5,
):
    """Умный поиск шаблонов для сообщения (используется в чате оператора)."""

@router.post("/{template_id}/use")
async def log_template_use(
    template_id: str, message_id: int,
    operator_approved: bool | None = None,
    final_text: str | None = None,
    response_time_ms: int = 0,
):
    """Записать использование шаблона (для статистики)."""

@router.post("/{template_id}/approve")
async def approve_learned_template(template_id: str):
    """Одобрить learned → business."""

# --- Stats & Import/Export ---
@router.get("/stats")
async def get_template_stats(period: str = "30d", category: str | None = None):
    """Аналитика для дашборда."""

@router.post("/import")
async def import_templates(file: UploadFile, scope: str = "business"): ...

@router.get("/export")
async def export_templates(scope: str | None = None, category: str | None = None,
                           format: str = "xlsx"): ...
```

---

### B6. Web UI (React)

**Файлы:**
- `packages/web/frontend/src/pages/Templates.tsx` (новый)
- `packages/web/frontend/src/components/TemplateEditor.tsx` (новый)
- `packages/web/frontend/src/components/TemplateSelector.tsx` (новый)

**Экраны (см. UI-макеты в задании):**
1. **Список шаблонов** — таблица с фильтрацией, поиском, группировкой по категориям
2. **Редактор** — модальное окно с WYSIWYG, подсказками переменных, предпросмотром
3. **Виджет в чате** — предложение шаблонов при ответе оператору
4. **Дашборд статистики** — успешность, тренды, проблемные шаблоны
5. **Импорт/экспорт** — загрузка/выгрузка Excel

**Ключевые компоненты React (схематично):**
```tsx
// TemplateEditor — модалка
<TemplateEditor
  template={editingTemplate}
  variables={["name", "order", "date", "address", "product", "price", "company"]}
  onSave={(data) => {}}
  onDelete={() => {}}
/>

// TemplateSuggest — виджет в чате
<TemplateSuggest
  message={currentMessage}
  category={detectedCategory}
  entities={extractedEntities}
  onSelect={(template) => fillReply(template)}
/>

// TemplateStats — дашборд
<TemplateStats
  period="30d"
  onPeriodChange={(p) => {}}
/>
```

---

### B7. Интеграция Pipeline + Template

```python
# Внутри Pipeline.process():
def process(self, text: str, context: ProcessingContext) -> PipelineResult:
    t0 = time_ms()

    # 1. Cache
    cached = self._cache.get(text)
    if cached:
        return cached

    # 2. Preprocess
    text = self._extractor.normalize(text)

    # 3. Classify
    category, confidence = self._classifier.predict(text)
    is_order, _ = self._classifier.predict_order(text)

    # 4. Extract entities
    entities = self._extractor.extract(text)

    # 5. RAG retrieval
    rag_results = self._retriever.retrieve(text) if self._retriever else []

    # 6. Select template
    rag_result = rag_results[0] if rag_results else None
    template = self._template_selector.select(text, category, entities,
                                              confidence, rag_result)

    # 7. Fill template
    reply_text = self._fill_template(template, entities) if template else None

    # 8. Determine need_human
    need_human = (confidence < 0.6) or (template and template.scope == "system"
                  and category == "complaint" and confidence < 0.8)

    result = PipelineResult(
        category=category,
        confidence=confidence,
        need_human=need_human,
        reply_text=reply_text,
        reply_source=template.scope if template else "fallback",
        entities=entities,
        is_order=is_order,
        template_id=template.id if template else None,
        processing_time_ms=time_ms() - t0,
    )

    # 9. Cache
    self._cache.set(text, result)

    return result
```

---

## План реализации по итерациям

### Итерация 1 — MVP (2 недели)

| Что | Кто | Файлы | Зависимости |
|---|---|---|---|
| HashingVectorizer + SGD (3 классификатора) | core-dev | `classifier.py` | scikit-learn |
| Regex экстрактор | core-dev | `extractor.py` | — |
| Pipeline оркестратор | core-dev | `pipeline.py` | classifier + extractor |
| Response cache | core-dev | `cache.py` | — |
| TrainingLog модель + batch trainer | core-dev | `training.py` | SQLAlchemy |
| Template модель + CRUD store | core-dev | `templates/store.py`, models.py | SQLAlchemy + SQLite |
| System template sync | core-dev | `templates/sync.py` | JSON config |
| API CRUD endpoints | web-dev | `packages/web/.../routers/templates.py` | FastAPI + TemplateStore |
| Web UI (список + редактор) | web-dev | `Templates.tsx`, `TemplateEditor.tsx` | React |
| — | — | — | — |
| CLI команды (status, retrain, accuracy) | core-dev | `plugin.py` | — |
| Обновление `plugin.py` (регистрация pipeline) | core-dev | `plugin.py` | всё выше |
| Обновление `messages.py` (reprocess-chatbot) | web-dev | `routers/messages.py` | pipeline |
| Обновление Telegram handler | core-dev | `handlers.py` | pipeline |
| Удаление `providers/`, `chatbot_service.py`, `prompt.py` | core-dev | — | — |
| Обновление `pyproject.toml` | core-dev | `pyproject.toml` | — |
| Генератор синтетики | core-dev | `scripts/generate_synthetic.py` | — |
| Тесты (module-level) | core-dev/web-dev | `tests/` | pytest |

### Итерация 2 — Аналитика + Качество (1 неделя)

| Что | Кто | Файлы |
|---|---|---|
| DriftMonitor | core-dev | `monitoring.py` |
| Дашборд статистики шаблонов | web-dev | `TemplateStats.tsx` |
| Widget выбора шаблона в чате | web-dev | `TemplateSelector.tsx` |
| Импорт/экспорт Excel | web-dev | `routers/templates.py` |
| Approve learned → business | web-dev | REST + UI кнопка |

### Итерация 3 — Харденинг (1 неделя)

| Что | Кто | Файлы |
|---|---|---|
| FAISS index rebuild nightly | core-dev | `rag/retriever.py` |
| Ночной retrain классификатора | core-dev | `training.py` |
| Модельный backup перед retrain | core-dev | `training.py` |
| Copy-on-write для FAISS rebuild | core-dev | `rag/vector_store.py` |
| Интеграционные тесты | core-dev | `tests/integration/` |

---

## Критерии приёмки (глобальные)

1. **Все 87 существующих тестов core проходят** (регрессия)
2. Pipeline обрабатывает сообщение за < 50 ms (без кэша) / < 1 ms (с кэшем)
3. Классификатор достигает accuracy > 85% за 7 дней (с синтетикой с первого дня > 70%)
4. Шаблоны: CRUD через UI + suggest endpoint работают
5. Кэш выдаёт hit на 80% повторяющихся сообщений
6. Telegram handler сохраняет все поля (category, need_human, auto_reply_text)
7. Нет зависимости от `llama-cpp-python`
8. Обучение: batch fit каждые 50 записей, nightly retrain
9. При accuracy < 70% — WARNING в лог
10. Системные шаблоны не удаляются через UI, синхронизируются из конфига

---

## Что НЕ входит в этот SPEC (будущие задачи)

- A/B тестирование шаблонов
- Роли пользователей (admin/manager/operator)
- Сложные условия (время суток, день недели, тип клиента)
- История изменений template_history
- JWT-аутентификация (сейчас API-key)
- Большие генеративные модели (ONNX с Phi/Qwen и т.п.) — не нужны при RAG-first подходе
