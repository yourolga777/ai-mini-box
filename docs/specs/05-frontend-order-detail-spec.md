# Спецификация: Страница заказа `/orders/:id` + OrderItem UI

**Разработчик:** Фронтенд-разработчик

**Файлы:**
- `packages/web/frontend/src/pages/OrderDetail.tsx` — новый
- `packages/web/frontend/src/App.tsx` — роутинг
- `packages/web/frontend/src/pages/Orders.tsx` — доработка

## 1. Маршрут

```tsx
<Route path="orders/:id" element={<OrderDetail />} />
```

## 2. Компонент OrderDetail

### Шапка
- Заголовок: «Заказ #42»
- Статус цветным бейджем: Новый / В обработке / Выполнен / Отменён
- Выпадающий список для смены статуса
- Кнопка «Удалить» (с подтверждением)

### Блок контакта
- Имя контакта → ссылка на `/contacts/:id`
- Если нет контакта — кнопка «Привязать контакт»

### Блок сообщения
- Если `source_message_id` есть → ссылка «Из сообщения #123» → `/messages/123`
- Если нет — «Создан вручную»

### Блок позиций заказа (OrderItems)

```tsx
<section>
  <h2>Позиции заказа</h2>
  <table>
    <thead>
      <tr>
        <th>Товар</th>
        <th>Кол-во</th>
        <th>Цена</th>
        <th>Сумма</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {items.map(item => (
        <tr key={item.id}>
          <td>{item.product_name}</td>
          <td>{item.quantity}</td>
          <td>{formatPrice(item.price_kopecks)}</td>
          <td>{formatPrice(item.quantity * item.price_kopecks)}</td>
          <td><button onClick={deleteItem}>&#10005;</button></td>
        </tr>
      ))}
    </tbody>
    <tfoot>
      <tr>
        <td colSpan={3}>Итого:</td>
        <td>{formatPrice(total)}</td>
        <td></td>
      </tr>
    </tfoot>
  </table>
  <button onClick={openAddModal}>+ Добавить позицию</button>
</section>
```

### Модалка добавления/редактирования позиции
- Поиск товара (автодополнение из каталога продуктов)
- Если выбран товар — цена и название подставляются автоматически
- Поля: название товара, количество, цена за единицу

### Блок заметок
- `notes` в textarea
- Автосохранение при потере фокуса

### Даты
- Создан: `formatDate(order.created_at)`
- Обновлён: `formatDate(order.updated_at)`

### Состояния
| Состояние | Что показываем |
|---|---|
| Loading | Skeleton |
| 404 | «Заказ не найден» + кнопка назад |
| Network error | Toast + кнопка повтора |
| Empty items | Заглушка «Нет позиций» |

## 3. Форматтеры

```typescript
function formatPrice(kopecks: number): string {
  return `${(kopecks / 100).toLocaleString('ru-RU', {minimumFractionDigits: 2})} ₽`;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    new: 'Новый',
    processing: 'В обработке',
    completed: 'Выполнен',
    cancelled: 'Отменён',
  };
  return labels[status] || status;
}
```

## 4. Доработка Orders.tsx

- Строки таблицы — ссылки на `/orders/:id`
- Вместо `contact_id` — имя контакта
- Колонка «Дата» (`created_at`)
- Фильтр по статусу (select)
- Поиск по заметкам (search input)

## 5. Критерии приёмки

- `/orders/:id` открывается и отображает заказ
- Позиции загружаются и отображаются с суммой
- Можно добавить, изменить, удалить позицию
- Статус меняется через выпадающий список
- Список заказов имеет ссылки на детали
- Форматтеры работают корректно
- Состояния loading/error/empty обработаны
