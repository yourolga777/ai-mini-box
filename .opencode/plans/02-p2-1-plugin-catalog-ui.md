# Спецификация P2-1 — Каталог плагинов и UI с табами

## Связанные пункты

- Бэкенд: `01-backend-spec.md` → **п.9** (API каталога плагинов и обновлений)
- Фронтенд: `00-frontend-spec.md` → **п.7** (UI плагинов: установленные vs доступные + обновления)

---

## 1. Бэкенд

### 1.1 PluginCatalog.get_status() — has_update

**Файл:** `packages/core/ai_mini_box/core/services/plugin_catalog.py`

**Что сделать:**
- Добавить `from packaging.version import Version`
- В `get_status()`, после определения `installed_version`, добавить сравнение:
  ```python
  if entry["installed"] and entry.get("version"):
      try:
          entry["has_update"] = Version(entry["version"]) > Version(entry["installed_version"])
      except Exception:
          entry["has_update"] = False
  else:
      entry["has_update"] = False
  ```

**Критерии приёмки:**
- `has_update=true` только если `version` в каталоге больше `installed_version`
- Сравнение через `packaging.version.Version` (семантическое)
- Если версии нет или ошибка — `has_update=false`

---

### 1.2 GET /api/plugins/catalog

**Файл:** `packages/web/ai_mini_box_web/routers/plugins.py`

**Что сделать:**
- Импортировать `PluginCatalog` из `ai_mini_box.core.services.plugin_catalog`
- Добавить эндпоинт **до** `/{name}`:
  ```python
  @router.get("/catalog")
  def list_catalog():
      catalog = PluginCatalog()
      return catalog.get_status()
  ```

**Критерии приёмки:**
- Возвращает список плагинов из каталога
- Каждый элемент: `name`, `description`, `version`, `installed`, `installed_version`, `has_update`
- Роут не перехватывается `/{name}`

---

### 1.3 GET /api/plugins — обогатить ответ

**Файл:** `packages/web/ai_mini_box_web/routers/plugins.py`

**Что сделать:**
- В `list_plugins()` построить `dict[name -> catalog_entry]` через `PluginCatalog().get_status()`
- Для каждого плагина добавить: `description` (или ""), `version` (или None), `has_update` (или false)

**Критерии приёмки:**
- Ответ содержит `description`, `version`, `has_update`
- Старые поля (`name`, `module`, `status`, `pid`) сохраняются

---

### 1.4 POST /api/plugins/{name}/update

**Файлы:** `routers/plugins.py`, `services/plugin_manager.py`

**В PluginManager:**
```python
def update_plugin(self, name: str) -> dict:
    pip_name = f"ai-mini-box-{name}"
    cmd = self._pip_install_args() + ["--upgrade", pip_name]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Update timed out after 120 seconds"}
    except Exception as e:
        return {"success": False, "output": str(e)}
    self._invalidate()
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}
```

**В роутере:**
```python
@router.post("/{name}/update")
def update_plugin(name: str):
    if not _manager.get_plugin(name):
        raise HTTPException(404, detail=f"Plugin '{name}' not found")
    return _manager.update_plugin(name)
```

**Критерии приёмки:**
- 200 + success для существующего
- 404 для несуществующего
- Используется `pip install --upgrade`

---

### 1.5 Тесты

**Файл:** `packages/web/tests/test_api_plugins.py`

- `test_catalog_returns_list` — `GET /api/plugins/catalog` → 200, list
- `test_catalog_has_status_fields` — каждый элемент: `name`, `installed`, `has_update`
- `test_catalog_not_found_plugin` — `installed=false`, `has_update=false`
- `test_update_success` — мок get_plugin + update_plugin
- `test_update_not_found` — 404
- Обогатить `test_list_plugins` — проверить `description`, `version`, `has_update` в ответе

---

## 2. Фронтенд

### 2.1 API client — новые методы

**Файл:** `packages/web/frontend/src/api/client.ts`

```typescript
export interface CatalogPlugin {
  name: string;
  description: string;
  version: string | null;
  installed: boolean;
  installed_version: string | null;
  has_update: boolean;
}
```

```typescript
catalogPlugins: () => request<CatalogPlugin[]>("/api/plugins/catalog"),
updatePlugin: (name: string) =>
  request<{ success: boolean; output: string }>(`/api/plugins/${name}/update`, { method: "POST" }),
```

---

### 2.2 Страница Plugins.tsx — переписать

**Файл:** `packages/web/frontend/src/pages/Plugins.tsx`

**Два таба:** «Установленные» (default) | «Доступные»

**Установленные** (`useQuery(["plugins"], () => api.list<any>("plugins"))`):
- Карточка: цветной индикатор статуса (зелёный=running, серый=installed), имя, описание, версия, статус текстом
- Кнопки: «Запустить» / «Остановить», «Обновить» (если `has_update`), «Удалить» (с confirm)
- Пусто: «Нет установленных плагинов»

**Доступные** (`useQuery(["catalog"], () => api.catalogPlugins())`):
- Карточка: имя, описание, версия
- Кнопка «Установить» (если `!installed`, открывает InstallModal)
- Если установлен: «Установлено v{version}»
- Пусто: «Нет доступных плагинов»

**Кнопка «+ Установить плагин»** — над табами, открывает InstallModal.

**После любого действия:** `qc.invalidateQueries(["plugins"])` + `qc.invalidateQueries(["catalog"])`.

**InstallModal** — без изменений.

---

## 3. Архитектурные заметки

- `PluginCatalog` уже реализован, только добавить `has_update`
- `packaging` доступен (транзитивная зависимость)
- Порядок роутов: `/catalog`, `/check/package`, `/config`, `/install` — до `/{name}`
- `PluginManager` не хранит `version`/`has_update` — приходят из каталога
- Два разных типа ответов: `InstalledPlugin` vs `CatalogPlugin`
