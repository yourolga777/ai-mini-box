# Инструмент: ingest-laws

## Описание

Загрузка юридических документов в базу знаний RAG-юриста. Принимает CSV или JSON с текстами законов, разбивает на чанки, создаёт эмбеддинги и индексирует в FAISS.

### Команда

```bash
ai-mini-box ingest-laws COMMAND [OPTIONS]
```

### Подкоманды

| Команда | Описание |
|---------|----------|
| `file` | Загрузить один файл |
| `dir` | Загрузить все файлы из директории |
| `clear` | Очистить индекс и БД |
| `status` | Статистика — сколько законов загружено |

### Опции

**`ingest-laws file`:**
- `--input PATH` — CSV или JSON файл (обязательно)
- `--chunk-size N` — размер чанка в символах (default: 512)
- `--chunk-overlap N` — перекрытие чанков (default: 64)
- `--rebuild` — перестроить индекс с нуля

**`ingest-laws dir`:**
- `--dir PATH` — директория с файлами (обязательно)
- `--pattern GLOB` — маска файлов (default: *.csv)
- `--recursive` — рекурсивно

### Формат входных данных

**CSV:**
```csv
title,text,source
"ГК РФ ст. 1","Основные начала гражданского законодательства...","consultant.ru"
"ЗоЗПП ст. 1","Правовое регулирование отношений...","consultant.ru"
```

**JSON:**
```json
[
  {"title": "ГК РФ ст. 1", "text": "...", "source": "consultant.ru"},
  {"title": "ЗоЗПП ст. 1", "text": "...", "source": "consultant.ru"}
]
```

### Примеры

```bash
ai-mini-box ingest-laws file --input laws.csv
# → ✅ Processed laws.csv: 45 documents → 128 chunks → FAISS index (128 vectors)

ai-mini-box ingest-laws status
# → 📚 Всего законов: 128 чанков
#   Источники: consultant.ru (45), garant.ru (30)

ai-mini-box ingest-laws clear
# → ✅ Index cleared (128 chunks удалены)
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `ingest-laws` для загрузки юридических документов в RAG-индекс.

### Требования:
1. Typer с подкомандами: `file`, `dir`, `clear`, `status`
2. Chunking: разбивка текста на перекрывающиеся куски (`--chunk-size`, `--chunk-overlap`)
3. Embedding: через SentenceTransformer ("paraphrase-multilingual-MiniLM-L12-v2")
4. Индексация: через `FaissVectorStore` из `infrastructure/vector_store/faiss_store.py`:
   - `index_documents(docs: list[LawDoc])`
   - `save(path)`
5. Сохранение в БД: через `SqliteLawRepo` из `infrastructure/database/repositories/law_repo.py`
6. CSV: столбцы title, text, source (обязательно)
7. JSON: массив объектов с полями title, text, source
8. `clear`: удалить все записи из БД и сбросить FAISS-индекс
9. `status`: показать количество чанков и источники
10. `--rebuild`: очистить и перестроить с нуля

### Архитектура:
- Файл: `ai_mini_box/tools/ingest_laws.py`
- Регистрация: `def register(app: typer.Typer)` — `app.add_typer(ingest_app, name="ingest-laws")`
- Использует sentence-transformers для эмбеддингов
- Использует FAISS для векторного индекса
- Сохраняет метаданные в БД (через LawRepo)
- Зависимости: sentence-transformers, faiss-cpu

### Тесты:
1. Unit: chunking текста на заданный размер
2. Unit: парсинг CSV с колонками title/text/source
3. Unit: clear очищает индекс
4. Integration: CliRunner — file → status → clear
5. Smoke: --help

### Структура файла:
```
tools/ingest_laws.py
```

### Пример желаемого поведения:
```
$ ai-mini-box ingest-laws file --input laws.csv
Processing laws.csv: 45 docs → 128 chunks
Embedding chunks... done (128 vectors)
Indexing FAISS... done
✅ 128 chunks indexed

$ ai-mini-box ingest-laws status
📚 128 chunks indexed
   consultant.ru: 45 docs
   garant.ru: 30 docs
Vector store: data/models/law_index (1.2 MB)

$ ai-mini-box ingest-laws dir --dir laws/ --pattern "*.csv" --recursive
Processing 3 files:
  laws/civil.csv: 45 docs → 128 chunks
  laws/admin.csv: 30 docs → 85 chunks
  laws/consumer.csv: 20 docs → 60 chunks
✅ Total: 95 docs → 273 chunks
```
```

