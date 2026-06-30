# Спецификация: Фронтенд — Бизнес-конфиг и чатбот-интеграция (v2)

> **Статус: РЕАЛИЗОВАНО** (июнь 2026)
> - BusinessSettings страница — ✅
> - Колонка "Категория" с цветными бейджами в Messages.tsx — ✅
> - Фильтр по категории — ✅
> - Блоки "Автоответ" и "Требует оператора" в MessageDetail — ✅
> - Кнопка "Переобработать через ИИ" — ✅
> - API-клиент: getBusinessConfig, updateBusinessConfig, reprocessMessage — ✅
> - Тест-панель чатбота (опционально) — НЕ РЕАЛИЗОВАНО (не требуется)

**Разработчик:** Веб (frontend — React)  
**Приоритет:** P1  
**Статус:** К реализации  
**Зависит от:** 20-web-api (все эндпоинты)

---

## 1. Страница настроек бизнеса

**Новый файл или раздел:** `/settings/business`

### SPA-роут

В `App.tsx` добавить:
```tsx
<Route path="settings/business" element={<BusinessSettings />} />
```

В `Layout.tsx` добавить пункт в sidebar или вынести в Settings (если такой раздел есть).

### Форма BusinessConfig

Эндпоинт: `GET/PUT /api/business/config`

Поля формы (каждое с label и textarea/input):

| Поле | Тип ввода |
|---|---|
| `company_name` | text |
| `work_hours` | text |
| `delivery_info` | textarea (3 строки) |
| `return_policy` | textarea (3 строки) |
| `payment_methods` | textarea (3 строки) |
| `contacts` | textarea (3 строки) |
| `faq` | list: question + answer (редактируемый список) |

**FAQ-редактор:**
- Кнопка "+ Добавить вопрос"
- Каждая запись: поле "Вопрос" + поле "Ответ" + кнопка "×" (удалить)
- Drag to reorder (опционально)

**Кнопки:**
- "Сохранить" → PUT /api/business/config
- "Отмена" → сброс

**Валидация:** все поля опциональны (могут быть пустыми), но если FAQ имеет элементы — question и answer обязательны.

## 2. Сообщения — колонка "Категория"

**Файл:** `packages/web/frontend/src/pages/Messages.tsx`

Добавить колонку "Категория" в таблицу после "Тема":

| Значение | Цвет бейджа |
|---|---|
| ЗАКАЗ | синий (`#2563eb`) |
| ВОПРОС | зелёный (`#16a34a`) |
| ПРЕДЛОЖЕНИЕ | серый (`#6b7280`) |
| ЖАЛОБА | красный (`#dc2626`) |
| ФЛУД | оранжевый (`#ea580c`) |
| null/undefined | — (пусто) |

Если `need_human=true` → добавить иконку/бейдж "👤 Требует оператора" (красный).

Если `auto_replied=true` → добавить иконку "🤖 Автоответ" (зелёный).

**Фильтр:** выпадающий список "Категория" с вариантами: "Все", "ЗАКАЗ", "ВОПРОС", "ПРЕДЛОЖЕНИЕ", "ЖАЛОБА", "ФЛУД", "Требуют оператора".

## 3. MessageDetail — блоки чатбота

**Файл:** `packages/web/frontend/src/pages/MessageDetail.tsx`

### Блок "Автоответ" (если auto_replied=true)

```tsx
<div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
  <div className="text-sm font-medium text-green-700 mb-1">🤖 Автоматический ответ отправлен</div>
  <div className="text-sm text-green-600 whitespace-pre-wrap">{msg.auto_reply_text}</div>
</div>
```

### Блок "Требует оператора" (если need_human=true)

```tsx
<div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
  <div className="text-sm font-medium text-red-700">👤 Требует внимания оператора</div>
  {msg.operator_context && (
    <div className="text-xs text-red-500 mt-1">{msg.operator_context}</div>
  )}
</div>
```

### Блок "Категория"

Показать бейдж категории (цветной) и подкатегорию (если есть) рядом с темой.

### Кнопка "Переобработать"

```tsx
<button onClick={handleReprocess} className="...">
  🔄 Переобработать через ИИ
</button>
```

Вызывает `POST /api/messages/{id}/reprocess-chatbot`, обновляет данные на странице.

## 4. Тест-панель чатбота (опционально)

**Новый компонент или страница:** `/settings/chatbot-test`

- Текстовое поле "Введите сообщение"
- Кнопка "Отправить" → вызывает `POST /api/messages/{id}/reprocess-chatbot` с тестовым ID или новый эндпоинт `POST /api/business/chatbot-test`
- Отображает результат: категорию, ответ, need_human и т.д.

## 5. API Client

**Файл:** `packages/web/frontend/src/api/client.ts`

Добавить методы:
```ts
getBusinessConfig: () => request<BusinessConfig>("/api/business/config"),
updateBusinessConfig: (cfg: BusinessConfig) => request<BusinessConfig>("/api/business/config", { method: "PUT", body: cfg }),
reprocessMessage: (id: number) => request<any>(`/api/messages/${id}/reprocess-chatbot`, { method: "POST" }),
testChatbot: (text: string) => request<any>("/api/business/chatbot-test", { method: "POST", body: { text } }),
```

Добавить тип:
```ts
interface BusinessConfig {
  company_name: string;
  work_hours: string;
  delivery_info: string;
  return_policy: string;
  payment_methods: string;
  contacts: string;
  faq: Array<{ question: string; answer: string }>;
}
```

## Acceptance criteria

- Страница BusinessSettings загружается и отображает текущий конфиг
- Изменение полей → сохранение через PUT
- FAQ можно добавлять/удалять
- В Messages.tsx: колонка "Категория" с цветными бейджами
- Фильтр по категории в Messages.tsx
- В MessageDetail: блоки "Автоответ" и "Требует оператора"
- Кнопка "Переобработать через ИИ" работает
- API-клиент содержит все новые методы

## Scope exclude

- Не писать ChatbotService
- Не менять Telegram handler
- Не писать бэкенд-API (это задача 20-web-api)
