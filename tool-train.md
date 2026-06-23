# Инструмент: train

## Описание

Дообучение или инициализация классификатора тем на новых примерах. Позволяет адаптировать модель под специфику конкретного бизнеса.

Использует sentence-transformers для эмбеддингов + LogisticRegression для классификации. Результат сохраняется в pickle-файл для быстрой загрузки.

### Команда

```bash
ai-mini-box train [OPTIONS]
```

### Аргументы

| Аргумент | Тип | Описание |
|----------|-----|----------|
| `--data PATH` | PATH | Файл с обучающими данными (default: data/training/topics.json) |
| `--output PATH` | PATH | Куда сохранить модель (default: data/models/classifier.pkl) |
| `--model NAME` | STRING | SentenceTransformer модель (default: paraphrase-multilingual-MiniLM-L12-v2) |
| `--test-size FLOAT` | FLOAT | Доля тестовых данных (default: 0.2) |
| `--force` | FLAG | Перезаписать существующую модель |
| `--eval` | FLAG | Показать метрики после обучения |

### Формат обучающих данных (JSON)

```json
[
  {"text": "Сколько стоит доставка?", "topic": "Цены"},
  {"text": "Хочу заказать 2 шт", "topic": "Заказ"},
  {"text": "Товар пришёл сломанный", "topic": "Жалоба"},
  {"text": "Работаете в субботу?", "topic": "График"},
  {"text": "Здравствуйте", "topic": "Другое"}
]
```

### Примеры

```bash
ai-mini-box train
# → ✅ Model trained: 115 examples → accuracy: 1.0 (10 test)

ai-mini-box train --data my_topics.json --output custom_model.pkl --eval
# → ✅ Model trained: 200 examples
#   Accuracy: 0.97
#   F1-score: 0.96
#   Classes: Цены(45), Заказ(38), Жалоба(25), График(15), Другое(22)

ai-mini-box train --force
# → ⚠ Existing model will be overwritten
#   ✅ Model trained and saved
```

---

## Промпт для вайбкодинга

```markdown
Создай CLI-инструмент `train` для обучения/дообучения классификатора тем.

### Требования:
1. Typer-команда с опциями
2. Используй существующий скрипт `scripts/train_classifier.py` как основу:
   - Загрузка JSON с примерами (text + topic)
   - SentenceTransformer для эмбеддингов
   - LogisticRegression (multinomial, max_iter=1000)
   - Сохранение через joblib/pickle
3. Разделение на train/test (`--test-size`)
4. Метрики: accuracy, f1-score, classification_report (с `--eval`)
5. Сохранение: pickle pipeline (encoder + classifier)
6. `--force`: подтверждение перезаписи существующей модели
7. Вывод статистики: сколько примеров на каждый класс
8. Валидация: проверка, что в данных есть все 5 тем

### Архитектура:
- Файл: `ai_mini_box/tools/train.py`
- Регистрация: `def register(app: typer.Typer)` — одиночная команда
- Использует `Topic` enum из `ai_mini_box.core.models`
- Сохраняет модель в `data/models/classifier.pkl`
- Зависимости: sentence-transformers, sklearn, joblib

### Тесты:
1. Unit: проверка валидации входных данных (5 тем обязательны)
2. Unit: --force перезаписывает существующую модель
3. Unit: --eval выводит метрики
4. Integration: CliRunner — train с тестовым JSON
5. Smoke: --help

### Структура файла:
```
tools/train.py
```

### Пример желаемого поведения:
```
$ ai-mini-box train
Training classifier on 115 examples...
  Цены:    40
  Заказ:   30
  Жалоба:  20
  График:  10
  Другое:  15
✅ Model saved to data/models/classifier.pkl

$ ai-mini-box train --data my_data.json --eval
Training on 200 examples...
Accuracy: 0.97
             precision  recall  f1-score
  Цены         0.98     0.96     0.97
  Заказ        0.96     0.97     0.96
  Жалоба       0.95     0.95     0.95
  График       0.97     0.98     0.97
  Другое       0.96     0.96     0.96
✅ Model saved
```
```

