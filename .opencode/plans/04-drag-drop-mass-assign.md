# Спецификация: Drag & drop + массовое назначение папок

**Источник:** `docs/specs/04-frontend-drag-drop-spec.md`

**Разработчик:** Фронтенд-разработчик

---

## 1. Доработка drag & drop

### 1.1 Touch-поддержка

**Файлы:** `packages/web/frontend/src/components/Table.tsx`

**Что сделать:**
Добавить touch-события на `<tr>` элементы (параллельно с существующим `draggable`/`onDragStart`):

- `onTouchStart` — запомнить `rowId` в ref, создать кастомный плейсхолдер: `<div>` с `position:fixed`, полупрозрачный, с ID и первыми 50 символами текста
- `onTouchMove` — перемещать плейсхолдер за пальцем (`touch.clientX/Y`), вызывать `document.elementFromPoint()` для определения папки под пальцем; подсвечивать папку через callback `onDragOver`
- `onTouchEnd` — если палец над папкой → вызвать `onDrop(folderId)`, убрать плейсхолдер

**Новый пропс Table:** `onDragOver?: (folderId: number | null) => void` — чтобы Table мог сообщать FolderSidebar о hover при touch-драге.

**Критерии:** touch drag на iPad/Android Chrome, не ломает mouse drag.

### 1.2 Multiple-drag

**Файлы:** `packages/web/frontend/src/components/Table.tsx`, `src/components/FolderSidebar.tsx`, `src/pages/Messages.tsx`

**Table.tsx:**
- В `onDragStart`: если `selectedIds.size >= 2` и перетаскиваемая строка входит в `selectedIds` → передать JSON.stringify([...selectedIds])
- Если size < 2 → как сейчас, один ID

**FolderSidebar.tsx:**
- `handleDrop`: распарсить `dataTransfer.getData("text/plain")` — если JSON-массив, вызвать `onBatchDrop(folderId, ids)`
- Новый пропс: `onBatchDrop?: (folderId: number, ids: number[]) => void`

**Messages.tsx:**
- `batchDropMut` → вызывает `api.batchAssignCategories({ message_ids: ids, category_id: folderId })`
- После успеха: `invalidateQueries(["folders"])`, `invalidateQueries(["messages"])`, снять выделение

**Визуал:** при drag группы — `setDragImage(canvas)` с надписью «+N», `effectAllowed = "copy"`.

### 1.3 Визуальный плейсхолдер

**Файлы:** `packages/web/frontend/src/components/Table.tsx`

- Создать canvas в `onDragStart`: ширина 200px, высота 40px, текст с ID и первыми 50 символами (или «N сообщений» для группы)
- Вызвать `e.dataTransfer.setDragImage(canvas, 10, 10)`

### 1.4 FolderSidebar: дроп-зона

**Файлы:** `packages/web/frontend/src/components/FolderSidebar.tsx`

- На `dragOver`: `e.preventDefault()`, `setDragOverId(folderId)`, добавить CSS: фон цвета папки с opacity 0.1 + рамка того же цвета
- CSS transition 150ms
- Вся строка папки — зона дропа (уже так, просто улучшить визуал)

---

## 2. Массовое назначение (улучшения)

**Файлы:** `packages/web/frontend/src/pages/Messages.tsx`

- **Прогресс:** `batchAssignMut.isPending` → disabled селект + спиннер
- **Toast:** после `onSuccess` — краткое уведомление «N сообщений назначено в папку X» (через `window.alert` или простой div с таймером 3s)
- **Крестик** у счётчика «Выбрано N» — `onClick={() => setSelectedIds(new Set())}`
- **Escape** — `useEffect` с `onKeyDown`, снимает выделение
- **Чекбокс «Выбрать все»** — уже есть (`allChecked` в Table), работает на текущей странице

---

## 3. Сортировка папок (drag to reorder)

**Файлы:** `packages/web/frontend/src/components/FolderSidebar.tsx`, `src/api/client.ts`

**client.ts:**
```typescript
reorderFolders: (order: number[]) =>
  request<{ ok: boolean }>("/api/llm/folders/reorder", {
    method: "POST",
    body: JSON.stringify({ order }),
  }),
```

**FolderSidebar.tsx:**
- На каждой папке (кроме is_system) — drag handle `≡` (слева от цветного маркера)
- HTML5 drag & drop между папками (перетаскивание для изменения порядка)
- При drag: горизонтальная линия-плейсхолдер между элементами
- После drop: новый порядок → `api.reorderFolders(ids)` (массив ID в новом порядке)
- Оптимистичное обновление: сразу отсортировать локально
- При ошибке: откат порядка + toast

**Бэкенд (если нет):**
- `POST /api/llm/folders/reorder` с `{ "order": [1, 3, 2, 4] }` — обновляет `sort_order` у всех папок
- Файл: `packages/web/ai_mini_box_web/routers/llm_folders.py`

---

## 4. MessageDetail: оптимизация загрузки папок

**Файлы:** `packages/web/frontend/src/pages/MessageDetail.tsx`

**Проблема:** цикл `for (const f of folderList)` делает N запросов `GET /api/llm/folders/{id}/messages`.

**Решение:**
1. **Бэкенд:** новый эндпоинт `GET /api/messages/{id}/categories`:
   ```python
   @router.get("/{id}/categories")
   def get_message_categories(id: int):
       msg = message_repo.get(id)
       if not msg:
           raise HTTPException(404)
       # найти все MessageCategoryAssignment для этого message_id
       # присоединить MessageCategory, вернуть [{id, name, description, color, is_system}]
   ```
   Файл: `packages/web/ai_mini_box_web/routers/messages.py`

2. **Фронтенд:** заменить N запросов на один:
   ```typescript
   const { data: msgCategories } = useQuery({
     queryKey: ["msg-categories", id],
     queryFn: () => request<FolderAssign[]>("/api/messages/${id}/categories"),
   });
   ```

**Критерии:** вместо N запросов — 1, данные те же, LLM-плагин не обязателен.

---

## 5. Критерии приёмки (общие)

- Все существующие тесты проходят (70/70 backend)
- `npm run build` — 0 ошибок
- Touch drag работает на iPad/Android
- Multiple-drag назначает все выбранные сообщения
- Папки перетаскиваются для изменения порядка
- MessageDetail загружает папки одним запросом
