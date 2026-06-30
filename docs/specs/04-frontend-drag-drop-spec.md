# Спецификация: Drag & drop + массовое назначение папок

**Разработчик:** Фронтенд-разработчик

## 1. Доработка существующего drag & drop (нативный HTML5)

**Файлы:**
- `packages/web/frontend/src/components/Table.tsx`
- `packages/web/frontend/src/components/FolderSidebar.tsx`
- `packages/web/frontend/src/pages/Messages.tsx`

### 1.1 Touch-поддержка

Нативный HTML5 Drag & Drop **не работает на touch-устройствах**. Реализовать через touch-события:

**Принцип:**
- На `touchstart` на строке таблицы: запоминаем ID сообщения, создаём кастомный drag-плейсхолдер (абсолютно позиционированный полупрозрачный блок)
- На `touchmove`: перемещаем плейсхолдер за пальцем, определяем под каким элементом папки находится палец (`document.elementFromPoint()`)
- На `touchend`: если палец над папкой — вызываем `assignMessageCategory(messageId, folderId)`, убираем плейсхолдер

**Критерии приёмки:**
- Сообщение можно перетащить в папку на iPad/Android Chrome
- Touch-драг работает параллельно с мышью (не ломает mouse drag)
- Визуальная обратная связь: папка подсвечивается при наведении пальца
- Плейсхолдер перетаскиваемого сообщения виден

### 1.2 Multiple-drag (перетаскивание группы сообщений)

**Сейчас:** `draggable=true` на каждой строке, в `onDragStart` передаётся один `messageId`.

**Доработка:**
- Если выбрано 2+ сообщения (чекбоксы) и пользователь начинает drag одной из выбранных строк — перетаскиваются **все выбранные**
- `dataTransfer.setData("text/plain", JSON.stringify(selectedIds))` — передаём массив ID
- В `FolderSidebar.onDrop` — парсим массив, вызываем `batchAssignCategories({ message_ids, category_id })`
- Если выбрано 0-1 сообщение — поведение как сейчас (один ID)

**Визуал:**
- При drag выделенной группы — к стандартному drag-изображению добавить бейдж «+N»
- Курсор — `copy`

**Критерии приёмки:**
- Выделить 3 сообщения → перетащить одно на папку → все 3 назначены
- Выделить 1 сообщение → перетащить → назначено только оно
- Дубликаты игнорируются

### 1.3 Визуальный плейсхолдер

**Сейчас:** браузер показывает стандартное изображение строки.

**Доработка:**
- Кастомный плейсхолдер: компактный блок с ID и первыми 50 символами текста
- При multiple-drag: «3 сообщения»
- Использовать `dataTransfer.setDragImage(canvas, offsetX, offsetY)` с canvas

### 1.4 FolderSidebar: дроп-зона для всей папки

**Сейчас:** дроп работает на `<li>` папки.

**Доработка:**
- Вся область строки папки — зона дропа
- При `dragOver`: подсветка цветом папки (10% opacity background + рамка)
- CSS transition 150ms

## 2. Массовое назначение папок

**Файлы:**
- `packages/web/frontend/src/pages/Messages.tsx`

**Уже есть:** выпадающий список папок при выборе 2+ сообщений → `batchAssignCategories`.

**Улучшения:**
- Индикация прогресса при массовом назначении
- Toast по завершению: «15 сообщений назначено в папку X»
- Кнопка «Снять выделение» (крестик у счётчика «Выбрано N»)
- `Escape` — снимает выделение
- Чекбокс «Выбрать все» — только **текущая страница**

## 3. Сортировка папок (drag to reorder)

**Файлы:**
- `packages/web/frontend/src/components/FolderSidebar.tsx`

**Сейчас:** у `MessageCategory` есть поле `order`, но нет UI для изменения.

**Доработка:**
- На каждой папке (кроме системных) — drag handle (≡ иконка слева)
- При перетаскивании — горизонтальная линия между папками как плейсхолдер вставки
- После отпускания — `POST /api/llm/folders/reorder` с новым порядком
- Оптимистичное обновление UI
- При ошибке — откат + toast

## 4. MessageDetail: оптимизация загрузки папок

**Файл:** `packages/web/frontend/src/pages/MessageDetail.tsx`

**Проблема:** N запросов `GET /api/llm/folders/{id}/messages` для каждой папки.

**Решение:**
- Заменить на один вызов `GET /api/messages/{id}/categories`
- endpoint возвращает `[{ id, name, description, color, is_system }]`
- Если LLM-плагин не установлен — ответ `[]`

## 5. Архитектурные решения

| Решение | Выбор |
|---|---|
| Drag & drop | Нативный HTML5 + touch polyfill |
| Touch-драг | `touchstart/move/end` + `elementFromPoint()` |
| Multiple-drag | JSON.stringify массива ID в dataTransfer |
| Drag-плейсхолдер | `setDragImage(canvas)` |
| Сортировка папок | `POST /api/llm/folders/reorder` |
| Системные папки | Исключены из reorder и drag |
