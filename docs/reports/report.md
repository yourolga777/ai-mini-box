# Отчёт о выполненных задачах

**Дата:** 27.06.2026  
**Ветка:** main

---

## P2-1 — Каталог плагинов + UI

### Бэкенд
- `PluginCatalog.has_update` — проверка обновлений через `packaging.version.Version`
- `GET /api/plugins/catalog` — список доступных на PyPI пакетов с полями `installed`, `version_installed`, `has_update`
- `GET /api/plugins` — обогащён `description`, `version`, `has_update`
- `POST /api/plugins/{name}/update` — обновление плагина
- `PluginManager.update_plugin()` — скачивание + установка новой версии

### Фронтенд
- Страница `Plugins.tsx` переписана: два таба «Установленные» / «Доступные»
- Карточки плагинов с кнопками: запуск, остановка, обновление, удаление
- Модальное окно с логом обновления

### Тесты
- `TestCatalog` (3 теста) — проверка формата каталога, полей статуса, неустановленных плагинов
- `TestUpdate` (2 теста) — обновление существующего и ошибка для отсутствующего
- `test_list_plugins_enriched` — расширенная проверка списка

---

## P2-2 — Заказы (Order auto-create + UI)

### Бэкенд
- `Message.extracted_order_id` — новое поле в core-модели
- `MessageModel.extracted_order_id` — ORM-маппинг
- Alembic-миграция `f7a8b9c0d1e2`
- `GET /api/messages/{id}/order` — получение связанного заказа (200 + `null`, если нет)
- `POST /api/messages/{id}/create-order` — создание заказа из сообщения
- `GET /api/orders` — добавлен фильтр `contact_id`

### Фронтенд
- `api/client.ts` — методы `getMessageOrder`, `createOrder`, `getContactOrders`
- `MessageDetail.tsx` — блок заказа (карточка или модалка создания)
- `ContactDetail.tsx` — таблица заказов контакта
- `helpers.ts` — `formatPrice`, `statusLabel`

### Тесты
- `TestMessageOrders` (5 тестов) — получение null-заказа, 404, создание, дубликат, без контакта

---

## 04 — Drag & Drop, массовое назначение, MessageDetail

### Бэкенд
- `POST /api/llm/folders/reorder` — изменение порядка папок
- `GET /api/messages/{id}/categories` — получение папок сообщения (заменяет N запросов)

### Фронтенд
- **Table.tsx:**
  - Touch-события (`touchstart`/`touchmove`/`touchend`)
  - Множественное перетаскивание (если выбрано ≥2 чекбоксов — тащит все)
  - Кастомный drag-image через Canvas
  - Проп `onTouchDrop` для touch-устройств
- **FolderSidebar.tsx:**
  - `data-folder-id` атрибут для touch-детекции
  - Визуальное выделение при наведении (`ring-2`)
  - Reorder папок через drag-and-drop (`onReorder` → `api.reorderFolders`)
  - Поддержка JSON-массива ID в `dataTransfer` для множественного дропа
- **Messages.tsx:**
  - `Escape` снимает выделение
  - Прогресс «назначение…» при batchAssign
  - Toast-уведомление после назначения
  - Подключены `onReorder` и `onTouchDrop`
- **MessageDetail.tsx:**
  - Замена N запросов `getFolderMessages` на один `getMessageCategories`

---

## Итоги

| Показатель | Значение |
|---|---|
| Всего тестов | 81 / 81 пройдено |
| Frontend build | 0 errors |
| Новых файлов | 1 (миграция) |
| Изменено файлов | ~20 |
| Предсуществующие баги | `test_api_contacts.py` (7 тестов) — не вызывается `create_all` в `conftest.py` |
