# Инструмент: classify

## Описание

Классифицирует текст сообщения по 5 темам: **Цены**, **Заказ**, **Жалоба**, **График**, **Другое**.

Использует sentence-transformers (paraphrase-multilingual-MiniLM) + LogisticRegression. Работает полностью локально, ~13ms на сообщение.

### Команда

```bash
ai-mini-box classify [OPTIONS] TEXT
```

### Аргументы

| Аргумент | Тип | Описание |
|----------|-----|----------|
| `TEXT` | STRING | Текст сообщения для классификации |

### Опции

| Опция | Описание |
|-------|----------|
| `--json` | Вывод в JSON (для pipe-скриптов) |
| `--confidence` | Показывать confidence для всех тем, а не только top-1 |
| `--model DATA/MODELS/CLASSIFIER.PKL` | Путь к файлу обученной модели |
| `--training-data DATA/TRAINING/TOPICS.JSON` | Путь к обучающим данным |

### Примеры

```bash
ai-mini-box classify "Сколько стоит доставка?"
# → Тема: Цены (confidence: 0.97)

ai-mini-box classify --json "Хочу вернуть товар"
# → {"topic": "Жалоба", "confidence": 0.94}

ai-mini-box classify --confidence "Можно прийти в пятницу?"
# → Тема: График (0.92) | Другое: 0.05 | Заказ: 0.02 | Цены: 0.01 | Жалоба: 0.00
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `classify` для классификации текста по 5 темам (Цены, Заказ, Жалоба, График, Другое).

### Требования:
1. Используй Typer для CLI-интерфейса
2. Используй существующий класс `Classifier` из `infrastructure/llm/classifier.py`:
   - Класс принимает `model_path` (pickle-файл с pipeline sklearn) и `training_data_path` (JSON)
   - Метод `classify(text: str) -> tuple[Topic, float]` возвращает тему и confidence
   - Метод `classify_with_proba(text: str) -> dict[Topic, float]` возвращает confidence для всех тем
3. Lazy-load: модель загружается только при первом вызове
4. Флаг `--json` для JSON-вывода в stdout
5. Флаг `--confidence` для вывода всех тем с confidence
6. Обработка ошибок: если модель не найдена — понятное сообщение и ненулевой exit code
7. Директория с данными по умолчанию: `data/` в корне проекта

### Архитектура:
- Файл: `ai_mini_box/tools/classify.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(classify_app, name="classify")`
- Использует `Topic` enum из `ai_mini_box.core.models`
- Классификатор — внешняя зависимость (sentence-transformers)
- Lazy-load: модель загружается при первом вызове

### Тесты:
1. Unit: mock-классификатор — возвращает предопределённую тему
2. Unit: --json вывод валидный JSON
3. Unit: ошибка при отсутствии модели
4. Integration: CliRunner — classify текста
5. Smoke: --help

### Структура файла:
```
tools/classify.py
```

### Пример желаемого поведения:
```
$ ai-mini-box classify "Сколько стоит?"
Тема: Цены (confidence: 0.97)

$ ai-mini-box classify --json "Жалуюсь"
{"topic": "Жалоба", "confidence": 0.94}

$ echo $?
0

$ ai-mini-box classify --no-model
Error: Model file not found at data/models/classifier.pkl
$ echo $?
1
```
```

