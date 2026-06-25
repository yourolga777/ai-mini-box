# Команды LLM плагина

## `ai-mini-box llm status`

Показать статус LLM сервиса: провайдер, модель, активность.

## `ai-mini-box llm classify <text>`

Классифицировать сообщение по теме. Возвращает Topic (Цены, Заказ, Жалоба, График, Другое).

## `ai-mini-box llm draft <text> [--topic]`

Сгенерировать черновик ответа на сообщение. Опционально — указать тему.

## `ai-mini-box llm extract <text>`

Извлечь сущности из текста (телефон, имя, дата, адрес, номер заказа).

## `ai-mini-box llm download-model [model]`

Скачать GGUF-модель с Hugging Face. Пример:
```
ai-mini-box llm download-model Qwen/Qwen2.5-0.5B-Instruct-GGUF:q4_0
```

## `ai-mini-box llm ingest-kb`

Перестроить RAG-индекс из базы знаний. Используется после добавления записей в Knowledge Base.
