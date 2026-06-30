# Release 5.0 — План

**Дата:** 27.06.2026

## Состав релиза

| Spec | Название | Статус |
|---|---|---|
| 00–03 | Базовая функциональность (сообщения, контакты, заказы, LLM, Telegram) | Реализовано |
| 04-frontend | Drag & drop + массовое назначение папок | В разработке |
| 05-core | Модель OrderItem + репозиторий | Реализовано (87 тестов) |
| 05-web | API OrderItem + доработка Order | В разработке |
| 05-frontend | Страница заказа `/orders/:id` | В разработке |
| 06-core | AnalyticsService + CLI | В разработке |
| 06-web | API `/api/analytics/*` | В разработке |
| 06-frontend | Дашборд (Dashboard.tsx + Chart.js) | В разработке |
| 07-devops | Docker, compose, .env, CI | В разработке |
| 08-email-service | Email-плагин (IMAP + SMTP) | В разработке |
| 08-web | Email API + PluginManager | В разработке |
| 08-frontend | Email UI (страница настроек) | В разработке |
| 09-llm | LLM process-daemon (docker-демон) | В разработке |

## Отложено на 5.1

| Компонент | Причина |
|---|---|
| **Retention heatmap** (06-frontend) | Сложный canvas-компонент, мало пользы без исторических данных |
| **CLI PNG-вывод** (06-core, --output png) | matplotlib +10МБ, редкий сценарий |
| **CLI retention** (06-core) | Идёт вместе с heatmap |
| **Multi-user / роли** | Архитектурное решение отложено (админ + юзер) |

## Ключевые решения

1. OrderItem — только `list_by_order()`, без `list()`/`search()`. CASCADE при удалении Order.
2. `_recalc_total` — метод `SqliteOrderItemRepo`, не модульная функция.
3. `OrderItemRepo.delete_by_order()` не нужен — CASCADE.
4. `add_item()` не нужен — репозиторий сохраняет, не конструирует.
5. Docker — 3 образа (web, telegram, llm), общий volume `data`.
6. Email — только stdlib, без внешних зависимостей.
7. Прогноз без sklearn — пустой список `[]`, не null.
