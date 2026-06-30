# Спецификация: Универсальная форма настроек плагина

**Для:** frontend-разработчик + web-разработчик  
**Приоритет:** P3  
**Затрагиваемые плагины:** все плагины, у которых есть конфигурация (Telegram, LLM, Email и будущие)

---

## 1. Проблема

В справке (`08-plugins.md:33-35`) написано: «Нажмите «Настроить» — откроется форма с полями конфигурации». Сейчас форма настроек есть только для двух плагинов (Telegram, LLM) и жёстко зашита в `PluginDetail.tsx`.

При этом:
- Бэкенд предоставляет `POST /api/plugins/{name}/config` (универсальный эндпоинт в `plugins.py:80`)
- Но на фронтенде этот эндпоинт **нигде не вызывается** для плагинов, кроме Telegram
- Для новых плагинов (Email и др.) нет UI для ввода конфигурации

---

## 2. Требования

### 2.1 Описание конфигурации плагина

Каждый плагин должен декларировать свою конфигурацию. Способ описания:

**Вариант A (рекомендуемый):** Плагин возвращает JSON Schema своих настроек через метод:

```python
# в plugin.py
class MyPlugin:
    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API ключ", "format": "password"},
                "webhook_url": {"type": "string", "title": "URL вебхука", "format": "uri"},
                "poll_interval": {"type": "integer", "title": "Интервал опроса (сек)", "default": 60},
                "debug": {"type": "boolean", "title": "Режим отладки", "default": False},
            },
            "required": ["api_key"]
        }
```

**Вариант B (упрощённый):** Статический JSON-файл в пакете плагина `config.schema.json`.

Выбранный вариант нужно реализовать для Telegram и LLM плагинов (существующие формы перевести на общий механизм), а затем остальные плагины смогут добавлять схему.

### 2.2 API

- `GET /api/plugins/{name}/config-schema` — возвращает JSON Schema конфигурации плагина (новый эндпоинт)
- `GET /api/plugins/{name}/config` — возвращает текущие значения конфигурации (проверить, существует ли)
- `POST /api/plugins/{name}/config` — уже существует (`plugins.py:80`), принимает `{"key": "value", ...}`

### 2.3 Фронтенд: универсальная форма

Создать компонент `PluginConfigForm.tsx`, который:

- Получает JSON Schema и текущие значения
- Рендерит поля автоматически:
  - `string` → `<input type="text">`
  - `string` + `format: "password"` → `<input type="password">`
  - `string` + `format: "uri"` → `<input type="url">`
  - `integer` / `number` → `<input type="number">`
  - `boolean` → `<checkbox>`
  - `array` → список с кнопкой «+»
  - `enum` → `<select>`
- Валидирует обязательные поля (из `required`)
- По сабмиту: вызывает `POST /api/plugins/{name}/config`

### 2.4 Интеграция в PluginDetail.tsx

- Для Telegram и LLM плагинов: использовать `PluginConfigForm` вместо жёстко зашитых форм
- Для Email и других плагинов: кнопка «Настроить» открывает `PluginConfigForm`
- Если у плагина нет `config_schema` — кнопка «Настроить» не показывается

---

## 3. Acceptance criteria

- [ ] У каждого плагина есть метод `config_schema()` (или файл `config.schema.json`)
- [ ] `GET /api/plugins/{name}/config-schema` возвращает JSON Schema
- [ ] `PluginConfigForm` рендерит поля из схемы автоматически
- [ ] Форма валидирует обязательные поля
- [ ] После сохранения конфиг применяется (вызов `POST /api/plugins/{name}/config`)
- [ ] Для Telegram и LLM старые формы заменены на универсальную (поведение не изменилось)
- [ ] Если у плагина нет схемы — кнопка «Настроить» скрыта

---

## 4. Файлы

| Файл | Изменение |
|---|---|
| `packages/telegram/ai_mini_box_telegram/plugin.py` | Добавить `config_schema()` |
| `packages/llm/ai_mini_box_llm/plugin.py` | Добавить `config_schema()` |
| `packages/web/ai_mini_box_web/routers/plugins.py` | Добавить `GET /api/plugins/{name}/config-schema` (строка ~80) |
| `packages/web/frontend/src/components/PluginConfigForm.tsx` | **Создать** — универсальная форма из JSON Schema |
| `packages/web/frontend/src/pages/PluginDetail.tsx` | Заменить жёсткие формы на `PluginConfigForm` (строки ~200-450) |
| `packages/web/frontend/src/api/client.ts` | Добавить `getPluginConfigSchema()` |
