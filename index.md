# AI mini box 4.0 — Спецификация пакета инструментов

## Обзор

Редизайн архитектуры: вместо монолитного приложения — **пакет CLI-инструментов** (`pip install ai-mini-box`), каждый инструмент отвечает за одну функцию.

```bash
ai-mini-box classify    — Классификация текста по 5 темам (Цены/Заказ/Жалоба/График/Другое)
ai-mini-box draft       — Генерация черновика ответа через LLM
ai-mini-box lawyer      — RAG-юрист (вопросы по законам)
ai-mini-box serve       — Фоновый демон обработки сообщений
ai-mini-box email       — Работа с Email (test/poll/send)
ai-mini-box telegram    — Работа с Telegram (test/poll/send/webhook)
ai-mini-box search      — Поиск по истории сообщений, контактам, товарам
ai-mini-box report      — Отчёты и статистика (topics/timeline/export)
ai-mini-box contacts    — CRUD контактов + импорт/экспорт
ai-mini-box products    — CRUD товаров + импорт/экспорт
ai-mini-box config      — Управление конфигурацией
ai-mini-box backup      — Резервное копирование БД
ai-mini-box ingest-laws — Загрузка законов в RAG-индекс
ai-mini-box gui         — Запуск PyQt6-интерфейса
ai-mini-box train       — Обучение классификатора
```

## Сложность инструментов

| Инструмент | Сложность | Время | Зависимости | Приоритет |
|-----------|-----------|-------|-------------|-----------|
| `classify` | 🟢 Easy | 0.5 дня | sentence-transformers | 1 |
| `draft` | 🟡 Medium | 1 день | llama-cpp-python + GGUF | 2 |
| `lawyer` | 🟡 Medium | 1.5 дня | FAISS + LLM | 4 |
| `serve` | 🔴 Hard | 2 дня | всe зависимости | 3 |
| `email` | 🟡 Medium | 1 день | imaplib, smtplib | 3 |
| `telegram` | 🟡 Medium | 1 день | python-telegram-bot | 3 |
| `search` | 🟢 Easy | 0.5 дня | SQLAlchemy | 1 |
| `report` | 🟢 Easy | 0.5 дня | pandas, matplotlib | 2 |
| `contacts` | 🟢 Easy | 0.5 дня | SQLAlchemy | 1 |
| `products` | 🟢 Easy | 0.5 дня | SQLAlchemy | 1 |
| `config` | 🟢 Easy | 0.5 дня | JSON, DPAPI | 1 |
| `backup` | 🟢 Easy | 0.5 дня | sqlite3 | 2 |
| `ingest-laws` | 🟡 Medium | 0.5 дня | sentence-transformers, FAISS | 4 |
| `gui` | 🟢 Easy | 0.25 дня | PyQt6 (опционально) | 5 |
| `train` | 🟡 Medium | 1 день | sentence-transformers, sklearn | 3 |

## Структура пакета

```
ai_mini_box/
├── __init__.py
├── __main__.py                  # python -m ai_mini_box
├── cli.py                       # Typer app + общий callback
├── tools/
│   ├── __init__.py
│   ├── classify.py
│   ├── draft.py
│   ├── lawyer.py
│   ├── serve.py
│   ├── email.py
│   ├── telegram.py
│   ├── search.py
│   ├── report.py
│   ├── contacts.py
│   ├── products.py
│   ├── config.py
│   ├── backup.py
│   ├── ingest_laws.py
│   ├── gui.py
│   └── train.py
├── core/                        # переносится
├── infrastructure/              # переносится
└── service_layer/               # переносится
```

## Зависимости (pyproject.toml)

```toml
[project]
name = "ai-mini-box"
version = "4.0.0"
dependencies = [
    "typer>=0.12",
    "llama-cpp-python==0.3.28",
    "SQLAlchemy==2.0.36",
    "sentence-transformers==2.2.2",
    "faiss-cpu==1.14.2",
    "python-telegram-bot==22.7",
    "pandas>=3.0",
    "matplotlib>=3.10",
    "loguru>=0.7",
    "scikit-learn>=1.6",
]
[project.optional-dependencies]
gui = ["PyQt6>=6.5"]
[project.scripts]
ai-mini-box = "ai_mini_box.cli:app"
```

## Рекомендуемый порядок реализации

| Шаг | Инструменты | Результат |
|-----|-------------|-----------|
| 1 | cli skeleton + `config`, `contacts`, `products` | База: CRUD + конфиг работают |
| 2 | `search`, `classify` | Поиск и классификация |
| 3 | `serve`, `email`, `telegram` | Демон и каналы |
| 4 | `draft`, `report`, `backup` | Умные функции |
| 5 | `train`, `lawyer`, `ingest-laws` | RAG и обучение |
| 6 | `gui` | Графический интерфейс |
```

