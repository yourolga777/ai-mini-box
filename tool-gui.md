# Инструмент: gui

## Описание

Запуск графического интерфейса (PyQt6). Опциональный компонент — устанавливается только при `pip install ai-mini-box[gui]`.

Состоит из MainWindow с 6 вкладками, системного трея, мастера первого запуска и панели статуса.

### Команда

```bash
ai-mini-box gui [OPTIONS]
```

### Опции

| Опция | Описание |
|-------|----------|
| `--config PATH` | Путь к config.json |
| `--minimized` | Запуск свёрнутым в трей |
| `--style PATH` | Путь к QSS-файлу стилей |
| `--no-tray` | Без системного трея |
| `--no-single-instance` | Разрешить несколько окон |

### Примеры

```bash
ai-mini-box gui
# → Открывается окно AI mini box (6 вкладок)

ai-mini-box gui --minimized
# → Запускается в трее, окно не показывается

ai-mini-box gui --style dark.qss
# → Интерфейс с тёмной темой
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `gui` для запуска PyQt6-интерфейса.

### Требования:
1. Typer-команда без подкоманд
2. Сделать PyQt6 опциональной зависимостью: `import try/except` с понятной ошибкой
3. Используй существующие компоненты из `presentation/`:
   - `gui_main.py` — точка входа (QApplication + MainWindow)
   - `main_window.py` — MainWindow с QTabWidget
   - `service_thread.py` — ServiceThread для InboxService
   - `tabs/` — DialogsTab, ContactsTab, ProductsTab, LawyerTab, ReportsTab, SettingsTab
   - `widgets/` — StatusBar, SystemTray, ReplyPanel
   - `wizards/setup_wizard.py` — мастер первого запуска
4. `--minimized`: запуск с флагом Qt.WindowMinimized или скрыть окно
5. `--style`: загрузка QSS-файла для стилизации
6. `--no-tray`: отключить системный трей
7. Single instance: по умолчанию включён (CreateMutexW)
8. Если PyQt6 не установлен — ошибка: "GUI dependencies not installed. Run: pip install ai-mini-box[gui]"

### Структура файла:
```
tools/gui.py
```

### Пример желаемого поведения:
```
$ ai-mini-box gui
[INFO] Starting AI mini box GUI...
[INFO] Database initialized
[INFO] MainWindow: 6 tabs loaded

$ ai-mini-box gui --minimized
[INFO] Starting minimized to system tray...

$ ai-mini-box gui
Error: PyQt6 is not installed.
Run: pip install "ai-mini-box[gui]"
```
```

