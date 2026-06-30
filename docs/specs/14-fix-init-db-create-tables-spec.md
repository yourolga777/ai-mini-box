# Спецификация: Добавить create_all() в init_db()

**Для:** core-разработчик  
**Приоритет:** P1 (ломает тесты)  
**Затрагиваемые плагины:** все (общая инфраструктура БД)

---

## 1. Проблема

7 тестов `test_api_contacts.py` падают с `sqlite3.OperationalError: no such table: contacts`.

**Корень:** `init_db()` в `packages/core/ai_mini_box/infrastructure/database.py:25` создаёт engine и sessionmaker, но **не вызывает `Base.metadata.create_all()`**. Таблицы физически не создаются.

Остальные 81 тест web-пакета проходят случайно — их импорты триггерят `_ensure_tables()` LLM-плагина, который вызывает `Base.metadata.create_all()`. `test_api_contacts.py` не импортирует LLM-роутеры, поэтому таблиц нет.

---

## 2. Решение

Добавить одну строку в `init_db()`:

```python
def init_db(db_path: Optional[str | Path] = None):
    global _engine, _SessionLocal
    db_path = Path(db_path) if db_path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}", echo=False, connect_args={"check_same_thread": False})
    event.listen(_engine, "connect", _enable_sqlite_fk)
    _SessionLocal = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)  # <-- добавить
```

Это безопасно: `create_all()` идемпотентен (не пересоздаёт существующие таблицы).

---

## 3. Acceptance criteria

- [ ] `cd packages/web && python -m pytest tests/test_api_contacts.py -v` — 7 passed
- [ ] `cd packages/core && python -m pytest tests -v` — 103 passed (регрессия)
- [ ] `cd packages/web && python -m pytest tests -v --ignore=tests/test_api_contacts.py` — 81 passed
- [ ] `cd packages/llm && python -m pytest tests -v` — 77 passed

---

## 4. Файлы

| Файл | Изменение |
|---|---|
| `packages/core/ai_mini_box/infrastructure/database.py:31` | Добавить `Base.metadata.create_all(bind=_engine)` |
