# Спецификация: LLM — Core Rewrite (ML-ядро + Template Engine)

**Разработчик:** llm-developer  
**Приоритет:** P0  
**Статус:** К реализации  
**Зависит от:** Нет (замена существующего LLM-плагина)

---

## 0. Scope

Все изменения — только в `packages/llm/ai_mini_box_llm/`. Web API (server.py) и
Telegram handler описаны в отдельных spec (25, 26) и реализуются после этого.

---

## 1. Pipeline (новый)

**Файл:** `packages/llm/ai_mini_box_llm/pipeline.py`

Центральный оркестратор. Заменяет `ChatbotService` + прямое использование провайдеров.

```python
@dataclass
class ProcessingContext:
    text: str
    history: list[dict] = field(default_factory=list)
    user_name: str = ""
    category: str | None = None
    contact_id: int | None = None
    business_config: dict | None = None

@dataclass
class PipelineResult:
    category: str                         # ЗАКАЗ | ВОПРОС | ПРЕДЛОЖЕНИЕ | ЖАЛОБА | ФЛУД
    confidence: float                     # 0.0–1.0
    need_human: bool
    reply_text: str | None
    reply_source: str                    # template.scope: "system" | "business" | "learned" | "fallback"
    entities: dict[str, Any]
    is_order: bool
    template_id: str | None
    processing_time_ms: int

class Pipeline:
    def __init__(self, classifier, entity_extractor, template_store, retriever, cache):
        ...

    def process(self, text: str, context: ProcessingContext) -> PipelineResult:
        """
        1. cache.get(text) → hit? return
        2. preprocess (normalize)
        3. classifier.predict(text) → (category, confidence)
        4. classifier.predict_order(text) → (is_order, order_confidence)
        5. extractor.extract(text) → entities
        6. retriever.retrieve(text) → RAG results
        7. template_store.find_best(category, text, entities, confidence, rag_result) → template
        8. fill_template(template, entities) → reply_text
        9. need_human = (confidence < 0.6) or (template.scope=="system" and confidence<0.8)
       10. cache.set(text, result)
       11. return PipelineResult
        """
```

**Критерии приёмки:** < 50 ms без кэша, < 1 ms с кэшем. Не падает на пустом тексте.

---

## 2. Классификатор (новый)

**Файл:** `packages/llm/ai_mini_box_llm/classifier.py`

Ensemble из 3 SGDClassifier на едином HashingVectorizer.

```python
class ClassifierEnsemble:
    def __init__(self):
        self._vectorizer = HashingVectorizer(
            n_features=2**18, analyzer="char_wb",
            ngram_range=(2, 5), norm="l2", alternate_sign=False,
        )
        # 3 классификатора (без class_weight="balanced" — несовместим
        # с warm_start=True + partial_fit на одно-классовых батчах)
        self._category_clf = SGDClassifier(loss="log_loss", penalty="elasticnet",
            alpha=1e-4, max_iter=1000, tol=1e-3, warm_start=True)
        self._order_clf = SGDClassifier(  # same params
            loss="log_loss", penalty="elasticnet", ...)
        self._folder_clf = SGDClassifier(  # same params
            loss="log_loss", penalty="elasticnet", ...)
        self._category_classes: list[str] = []
        self._fitted = False

    def predict(self, text: str) -> tuple[str, float]: ...
    def predict_order(self, text: str) -> tuple[bool, float]: ...
    def predict_folder(self, text: str, folder_names: list[str]) -> str | None: ...
    def partial_fit_batch(self, texts: list[str], categories: list[str]): ...
    def fit_all(self, texts, categories, is_order, folder_labels=None): ...

    def save(self, path="data/classifier_model.pkl"): ...
    def load(self, path="data/classifier_model.pkl") -> bool: ...
```

**Холодный старт:** без обученной модели возвращает `("ВОПРОС", 0.0)`.
Синтетические данные (A8) генерируются при первом запуске.

**Критерии:** `predict("заказ пиццы")` → `("ЗАКАЗ", >0.6)`. Batch fit не падает при 1 записи.

---

## 3. Экстрактор сущностей (новый)

**Файл:** `packages/llm/ai_mini_box_llm/extractor.py`

Только regex. Заменяет `extract_entities()` + `extract_order_info()` из старого провайдера.

```python
class EntityExtractor:
    PHONE_RE = re.compile(r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}")
    DATE_RE = re.compile(...)   # 15.06.2026, завтра, через N дней
    TIME_RE = re.compile(...)   # 15:00, 3 часа дня
    ADDRESS_RE = re.compile(...) # ул., дом, кв.
    EMAIL_RE = re.compile(...)
    NAME_RE = re.compile(r"(?:меня зовут|я)\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)")

    NORMALIZE_MAP = {"прив": "привет", "спс": "спасибо", ...}

    def normalize(self, text: str) -> str: ...
    def extract(self, text: str) -> dict[str, Any]: ...
    def extract_order_items(self, text: str) -> list[dict]: ...
    def has_product_keywords(self, text: str) -> bool: ...
```

**Критерии:** `extract("+7 999 123-45-67")` → `{"phone": "+7 999 123-45-67"}`.
Не падает на None/пустой строке.

---

## 4. RAG (переписать)

**Файлы:**
- `rag/embeddings.py` — ONNX Runtime + all-MiniLM-L6-v2 (авто-загрузка)
- `rag/vector_store.py` — FAISS index вместо JSON
- `rag/retriever.py` — поиск с threshold

```python
class EmbeddingModel:
    ONNX_MODEL_URL = "https://huggingface.co/optimum/all-MiniLM-L6-v2/resolve/main/model.onnx"
    LOCAL_PATH = "data/embeddings/model.onnx"

    def __init__(self):
        self._session = onnxruntime.InferenceSession(str(self.LOCAL_PATH))

    def embed(self, text: str) -> list[float]: ...  # 384-dim

class FaissVectorStore:
    def __init__(self, dim=384, index_path="data/rag_index.faiss"):
        self._index = faiss.IndexFlatIP(dim)
        self._metadata: list[dict] = []

    def add(self, text, embedding, metadata): ...
    def search(self, query_vec, top_k=3, threshold=0.75) -> list: ...

class Retriever:
    def retrieve(self, text: str, top_k=3) -> list[tuple[str, float, dict]]: ...
    def add_successful_reply(self, question, answer, category): ...
    def rebuild_index(self, texts, metadatas):
        """Перестроение индекса через temp-файл (COW — copy-on-write):
        1. Создать временный FaissVectorStore с путём data/rag_index_tmp.faiss
        2. Построить новый FAISS index + metadata
        3. save() → shutil.move(tmp, main) — атомарная замена
        4. Заменить self._store на новый экземпляр
        Без copy.deepcopy in-memory (не удваивает RAM)."""
```

**Критерии:** RAM < 50 МБ на 10k записей. Поиск < 10 ms. Если модель не загрузилась → RAG отключён, лог WARNING. Rebuild через copy-on-write (временный файл).

---

## 5. Кэш (новый)

**Файл:** `packages/llm/ai_mini_box_llm/cache.py`

```python
class ResponseCache:
    def __init__(self, maxsize=1000, ttl_seconds=604800):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, text: str) -> PipelineResult | None: ...
    def set(self, text: str, result: PipelineResult): ...
    def invalidate(self, template_id: str): ...
    def stats(self) -> dict: ...
```

**Критерии:** hit rate > 80% на повторяющихся сообщениях. LRU-вытеснение при maxsize.

---

## 6. Обучение (новый)

**Файл:** `packages/llm/ai_mini_box_llm/training.py`

```python
class TrainingLog(Base):
    __tablename__ = "training_log"
    id: int (PK, autoincrement)
    message_text: str
    category_predicted: str | None
    category_corrected: str | None
    is_order_predicted: bool | None
    is_order_corrected: bool | None
    template_id_used: str | None
    operator_approved: bool | None
    operator_edited: bool | None
    final_reply_text: str | None
    created_at: datetime

class Trainer:
    def log_correction(self, message_text, category_corrected, category_predicted=None): ...
    def collect_batch(self, min_samples=50) -> tuple[list[str], list[str]]: ...
    def train_on_batch(self, texts, categories) -> dict: ...
    def auto_train(self): ...
```

**Batch fit:** при 50 новых записях → `train_on_batch()`.  
**Nightly retrain:** выполняется планировщиком (см. 6.1).  
**Критерии:** при 0 записях `auto_train()` не делает ничего. Перед retrain — backup модели.

---

### 6.1 Планировщик задач (APScheduler)

**Файл:** `packages/llm/ai_mini_box_llm/scheduler.py` (новый)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import atexit

class TaskScheduler:
    def __init__(self, db_url: str):
        self._scheduler = BackgroundScheduler(
            jobstores={"default": SQLAlchemyJobStore(url=db_url)},
            executors={"default": ThreadPoolExecutor(max_workers=2)},
            timezone="Europe/Moscow",
        )

    def setup(self):
        # 1. Nightly retrain (daily 02:00)
        self._scheduler.add_job(
            func=self._run_nightly_retrain,
            trigger=CronTrigger(hour=2, minute=0),
            id="nightly_retrain",
            max_instances=1,
            misfire_grace_time=3600,
        )
        # 2. Sync system templates (hourly)
        self._scheduler.add_job(
            func=self._sync_templates,
            trigger=CronTrigger(minute=0),
            id="sync_templates",
        )
        # 3. Rebuild RAG index (every 6h)
        self._scheduler.add_job(
            func=self._rebuild_rag_index,
            trigger=CronTrigger(hour="*/6", minute=0),
            id="rebuild_rag_index",
        )
        # 4. Cleanup old logs (weekly Sun 03:00)
        self._scheduler.add_job(
            func=self._cleanup_logs,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),
            id="cleanup_logs",
        )
        self._scheduler.start()

    def shutdown(self):
        self._scheduler.shutdown(wait=False)

    def _run_nightly_retrain(self):
        """1) backup модели → 2) retrain классификатора → 3) rebuild RAG →
        4) валидация → 5) деплой если точность > старой."""
    def _sync_templates(self):
        """Sync system templates из business_config.json в БД."""
    def _rebuild_rag_index(self):
        """Перестроение FAISS индекса через temp-файл (COW)."""
    def _cleanup_logs(self):
        """Удаление TrainingLog старше 90 дней."""
```

**4 задачи расписания:**

| ID | Триггер | Действие |
|---|---|---|
| `nightly_retrain` | Daily 02:00 | Backup → retrain classifier → rebuild RAG → validate → deploy if score improved |
| `sync_templates` | Hourly (:00) | Sync system templates from `business_config.json` |
| `rebuild_rag_index` | Every 6h | Rebuild FAISS index via temp-file COW |
| `cleanup_logs` | Weekly Sun 03:00 | Delete `TrainingLog` entries older than 90 days |

**Интеграция в plugin.py:**
```python
scheduler = TaskScheduler(db_url)
scheduler.setup()
atexit.register(scheduler.shutdown)
```

**Критерии:** При старте плагина запускаются 4 задачи. Ошибка одной не влияет на остальные. Graceful shutdown через `atexit`.

---

## 7. Мониторинг (новый)

**Файл:** `packages/llm/ai_mini_box_llm/monitoring.py`

```python
class DriftMonitor:
    def compute_accuracy(self, since_hours=168) -> float: ...
    def confusion_matrix(self, since_hours=168) -> dict: ...
    def category_distribution(self, since_hours=168) -> dict[str, int]: ...
    def accuracy_trend(self, days=30) -> list[dict]: ...
    def get_degraded_categories(self) -> list[str]: ...
    def report(self) -> dict: ...
```

**Критерии:** при accuracy < 70% — WARNING в лог.

---

## 8. Синтетические данные (новый)

**Файл:** `packages/llm/ai_mini_box_llm/scripts/generate_synthetic.py`

Генерация 500-1000 сообщений на категорию через шаблоны + рандомизацию (без LLM).

```python
def generate_synthetic_dataset() -> list[tuple[str, str, bool]]:
    # (text, category, is_order)
    ...
def generate_and_train(classifier: ClassifierEnsemble): ...
```

**CLI:** `ai-mini-box llm generate-synthetic [--count 500]`
**Критерии:** accuracy > 70% после генерации. Минимум 200 сообщений на категорию.

---

## 9. Модели (дополнить)

**Файл:** `packages/llm/ai_mini_box_llm/models.py` (добавить)

```python
class Template(Base):
    __tablename__ = "templates"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    scope = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
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
        if self.usage_count == 0: return 0.0
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

## 10. Template Store (новый)

**Файл:** `packages/llm/ai_mini_box_llm/templates/store.py`

Допустимые значения `scope`: `{"system", "business", "learned"}`.
- **system** — из `business_config.json`, read-only, синхронизация через `SystemTemplateSync`
- **business** — CRUD через REST API / UI
- **learned** — создаётся RAG-результатами, может быть одобрен → business

```python
class TemplateStore:
    def __init__(self, db_session_factory):
        self._db = db_session_factory

    def get(self, template_id: str) -> Template | None: ...
    def list(self, scope=None, category=None, is_active=True) -> list[Template]: ...
    def create(self, data) -> Template: ...
    def update(self, template_id, data) -> Template: ...
    def delete(self, template_id, hard=False): ...

    def find_best(self, category, text, entities, confidence, rag_result=None) -> Template | None:
        """1. system triggers → 2. business (category + vars in entities) → 3. RAG → 4. fallback"""
    def find_by_triggers(self, text) -> Template | None: ...
    def find_by_category(self, category, confidence, entities=None) -> Template | None:
        """Среди шаблонов по category: confidence >= confidence_min,
        все variables присутствуют в entities, сортировка по success_rate DESC"""
    def increment_usage(self, template_id, approved=None): ...
    def _get_fallback(self) -> Template: ...
```

**Алгоритм find_best (с проверкой переменных):**
```
1. Проверить system-триггеры (ключевые слова) → если найден, использовать
2. Business-шаблон: отфильтровать по category, confidence >= confidence_min,
   отсортировать по success_rate DESC; среди подходящих — первый,
   у которого все variables присутствуют в entities
3. RAG: similarity > 0.75
4. Fallback: "Я передал ваш запрос специалисту"
```

---

## 11. System Template Sync (новый)

**Файл:** `packages/llm/ai_mini_box_llm/templates/sync.py`

**Путь по умолчанию:** `data/business_config.json` (относительно CWD).  
Если файл не существует → `logger.warning()`, синхронизация пропущена.  
Файл создаётся и ведётся оператором вручную (системные шаблоны read-only, не через UI).

```python
class SystemTemplateSync:
    def __init__(self, db, config_path: Path = Path("data/business_config.json")):
        self.db = db
        self.config_path = config_path

    def sync_on_startup(self):
        """Синхронизация system-шаблонов из business_config.json в БД.
        - Если файла нет → WARNING, return
        - Новые → создать
        - Изменённые → version+1
        - Удалённые из JSON → is_archived=True
        - Никогда не удаляет из БД"""
```

**Пример business_config.json:**
```json
{
  "templates": {
    "system": {
      "legal_disclaimer": {
        "text": "Для расторжения договора обратитесь в офис.",
        "category": "complaint",
        "triggers": ["расторг", "отказ"],
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

## 12. Интеграция в plugin.py (переписать)

**Файл:** `packages/llm/ai_mini_box_llm/plugin.py`

```python
def register(app: typer.Typer) -> None:
    _ensure_tables()
    _seed_system_categories()

    try:
        classifier = ClassifierEnsemble()
        if not classifier.load():
            from .scripts.generate_synthetic import generate_and_train
            generate_and_train(classifier)

        extractor = EntityExtractor()

        embed_model = EmbeddingModel()
        vector_store = FaissVectorStore()
        retriever = Retriever(embed_model, vector_store)

        template_store = TemplateStore(...)
        SystemTemplateSync(db_session, config_path).sync_on_startup()

        cache = ResponseCache()
        # TemplateStore передаётся напрямую (TemplateSelector удалён — find_best в store)
        pipeline = Pipeline(classifier, extractor, template_store, retriever, cache)

        trainer = Trainer(classifier, get_db)
        monitor = DriftMonitor()

        scheduler = TaskScheduler(db_url)
        scheduler.setup()
        atexit.register(scheduler.shutdown)

        register_service("llm", pipeline)
        register_service("trainer", trainer)
        register_service("drift_monitor", monitor)
    except Exception as e:
        logger.warning("LLM plugin initialization failed: {}", e)
```

**CLI команды:**

| Команда | Действие |
|---|---|
| `ai-mini-box llm status` | Показать статус pipeline |
| `ai-mini-box llm classify <text>` | Классифицировать текст |
| `ai-mini-box llm extract <text>` | Извлечь сущности |
| `ai-mini-box llm generate-synthetic` | Сгенерировать синтетику |
| `ai-mini-box llm retrain` | Ручное переобучение |
| `ai-mini-box llm accuracy` | Показать accuracy за неделю |

`download-model` **удалён** — ONNX модель авто-загружается в EmbeddingModel.__init__().

---

## 13. AutoProcessor (переписать)

**Файл:** `packages/llm/ai_mini_box_llm/auto_processor.py`

```python
class AutoProcessor:
    def process(self, message, contact) -> AutoProcessResult:
        pipeline = get_service("llm")
        if pipeline is None or not message.text:
            return AutoProcessResult()

        p_result = pipeline.process(message.text, ProcessingContext(
            history=[], user_name=message.extracted_name or "", category=None
        ))

        # order creation
        if p_result.is_order:
            order = Order(contact_id=message.contact_id, notes=message.text, status="new")
            created = repos.orders.add(order)
            message.extracted_order_id = created.id

        # folder assignment
        folder_id = self._assign_llm_folder(repos, message, p_result.category)
        ...
```

---

## 14. Удалить

```
packages/llm/ai_mini_box_llm/providers/         # целиком
    base.py
    local.py
    remote.py
packages/llm/ai_mini_box_llm/chatbot_service.py
packages/llm/ai_mini_box_llm/prompt.py
```

---

## 15. pyproject.toml (обновить)

```toml
dependencies = [
    "ai-mini-box-core>=5.0.0",
    "scikit-learn>=1.3",
    "onnxruntime>=1.15",
    "faiss-cpu>=1.7",
    "apscheduler>=3.10",
]

[project.optional-dependencies]
remote = ["openai>=1.0"]
dev = ["pytest>=8"]

# Удалить:
# [project.optional-dependencies]
# local = ["llama-cpp-python>=0.2"]
# download = ["huggingface-hub>=0.20"]
```

---

## 16. Alembic миграция

**Единый Alembic в `packages/core/migrations/`.**  
Все модели (core + llm-плагин) наследуются от одного `Base` (`core.database.Base`).

**Настройка env.py:**
```python
# core/migrations/env.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.database import Base
from core.models import *  # noqa — таблицы ядра
from llm_plugin.models import *  # noqa — таблицы плагина (Template, TrainingLog...)

target_metadata = Base.metadata
```

**Создание миграции:**
```bash
alembic revision --autogenerate -m "add_templates_module"
# → core/migrations/versions/002_add_templates_module.py
```

**`create_all()` — только для тестов** (in-memory SQLite в `conftest.py`).
В продакшене — `alembic upgrade head`.

**Миграция 002_add_templates_module** включает таблицы:
- `templates` — см. SQL в п.9
- `template_usage_log`
- `training_log`
- Индексы: `idx_templates_scope_category_active`, `idx_usage_log_template_id`, `idx_usage_log_created_at`

---

## 17. Порядок реализации

| Шаг | Что | Файлы |
|---|---|---|
| 1 | Классификатор + синтетика | `classifier.py`, `scripts/generate_synthetic.py` |
| 2 | Экстрактор | `extractor.py` |
| 3 | Кэш | `cache.py` |
| 4 | RAG (ONNX + FAISS) | `rag/embeddings.py`, `rag/vector_store.py`, `rag/retriever.py` |
| 5 | Template модели + store + sync | `models.py`, `templates/store.py`, `templates/sync.py` |
| 6 | Pipeline | `pipeline.py` |
| 7 | Training + Monitoring | `training.py`, `monitoring.py` |
| 8 | Scheduler (APScheduler) | `scheduler.py` |
| 9 | plugin.py + авто-процессор | `plugin.py`, `auto_processor.py`, `pyproject.toml` |
| 10 | Удалить старое | `providers/`, `chatbot_service.py`, `prompt.py` |
| 11 | Миграция Alembic | `core/migrations/versions/002_add_templates_module.py` |

---

## 18. Критерии приёмки (LLM scope)

1. Классификатор предсказывает с accuracy > 70% после синтетики
2. Pipeline.process() отрабатывает за < 50 ms (без кэша)
3. RAG-поиск < 10 ms на 10k записей
4. Кэш: hit > 80% на повторяющихся сообщениях
5. Template CRUD работает через TemplateStore
6. SystemTemplateSync синхронизирует шаблоны при старте
7. Обучение: batch fit каждые 50 записей, Scheduler запускает nightly retrain (02:00)
8. Никаких зависимостей от `llama-cpp-python`, `huggingface-hub`, `sentence-transformers`
9. Все старые таблицы (llm_categories, llm_category_assignments) не затронуты
10. `ai-mini-box llm status` показывает состояние pipeline
