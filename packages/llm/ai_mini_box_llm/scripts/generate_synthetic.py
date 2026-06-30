from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from loguru import logger

PRODUCTS = [
    "ноутбук", "телефон", "планшет", "холодильник", "стиральная машина",
    "телевизор", "пылесос", "кофеварка", "микроволновка", "утюг",
    "наушники", "колонка", "клавиатура", "мышка", "монитор",
    "пицца", "роллы", "суши", "бургер", "картошка фри",
    "торт", "пирожное", "хлеб", "молоко", "сыр",
    "стол", "стул", "кровать", "шкаф", "диван",
]

ORDER_TEMPLATES = [
    "Здравствуйте! Хочу заказать {product}",
    "Мне нужно {n} {product}",
    "Закажите мне {product} пожалуйста",
    "Пришлите {n} {product} по адресу",
    "Хочу купить {product} в количестве {n} штук",
    "Заказать {product} с доставкой",
    "Можно заказать {product}?",
    "Нужно {n} {product}, сколько по времени?",
]

QUESTION_TEMPLATES = [
    "Здравствуйте, у меня вопрос",
    "Сколько стоит {product}?",
    "Когда приедет курьер?",
    "У вас есть в наличии {product}?",
    "Как оформить заказ?",
    "Какие способы оплаты?",
    "Сколько времени занимает доставка?",
    "Работаете ли вы в воскресенье?",
    "Есть ли у вас гарантия на {product}?",
    "Какой срок службы у {product}?",
    "Подскажите, какие есть модели",
    "Можно ли вернуть товар?",
    "Нужна ли предоплата?",
    "Сколько стоит доставка?",
    "Как связаться с оператором?",
]

COMPLAINT_TEMPLATES = [
    "У меня сломался {product}, хочу вернуть",
    "Пришёл бракованный {product}",
    "Заказ не пришёл, уже прошла неделя",
    "Курьер опоздал на 3 часа, это безобразие",
    "Товар не соответствует описанию",
    "Хочу оформить возврат денег",
    "Мне прислали не тот цвет",
    "Качество ужасное, прошу замену",
    "Доставка задержалась, я жду уже 5 дней",
    "Сломалось через день после покупки",
]

OFFER_TEMPLATES = [
    "Здравствуйте, предлагаю сотрудничество",
    "Хочу предложить вам свои услуги",
    "Мы можем поставлять {product} оптом со скидкой",
    "У нас есть выгодное предложение по {product}",
    "Предлагаю рекламу в нашем канале",
    "Давайте обсудим партнёрство",
    "Могу помочь с продвижением вашего бизнеса",
    "Есть предложение по совместной акции",
]

SPAM_TEMPLATES = [
    "Привет, как дела?",
    "Спасибо, всё отлично",
    "Ок, понял",
    "Да, хорошо",
    "Нет, спасибо",
    "Привет",
    "Здорова",
    "Как сам?",
    "Понял, принял",
    "Добрый день",
]


def generate_synthetic_dataset(count: int = 500) -> list[tuple[str, str, bool]]:
    random.seed(42)
    dataset: list[tuple[str, str, bool]] = []

    for _ in range(count):
        cat_roll = random.random()
        if cat_roll < 0.25:
            category = "ЗАКАЗ"
            template = random.choice(ORDER_TEMPLATES)
            product = random.choice(PRODUCTS)
            n = random.randint(1, 10)
            text = template.format(product=product, n=n).capitalize()
            is_order = True
        elif cat_roll < 0.50:
            category = "ВОПРОС"
            template = random.choice(QUESTION_TEMPLATES)
            product = random.choice(PRODUCTS)
            text = template.format(product=product).capitalize()
            is_order = False
        elif cat_roll < 0.70:
            category = "ЖАЛОБА"
            template = random.choice(COMPLAINT_TEMPLATES)
            product = random.choice(PRODUCTS)
            text = template.format(product=product).capitalize()
            is_order = False
        elif cat_roll < 0.85:
            category = "ПРЕДЛОЖЕНИЕ"
            template = random.choice(OFFER_TEMPLATES)
            product = random.choice(PRODUCTS)
            text = template.format(product=product).capitalize()
            is_order = False
        else:
            category = "ФЛУД"
            template = random.choice(SPAM_TEMPLATES)
            text = template.capitalize()
            is_order = False

        dataset.append((text, category, is_order))

    return dataset


def generate_and_train(classifier) -> None:
    logger.info("Generating synthetic dataset...")
    dataset = generate_synthetic_dataset(count=500)
    texts = [item[0] for item in dataset]
    categories = [item[1] for item in dataset]
    is_order = [item[2] for item in dataset]

    classifier.fit_all(texts, categories, is_order)
    classifier.save()

    train_correct = sum(1 for t, c in zip(texts, categories) if classifier.predict(t)[0] == c)
    train_accuracy = train_correct / len(texts) if texts else 0.0
    logger.info("Synthetic training complete: {} samples, accuracy {:.1%}", len(texts), train_accuracy)

    out = Path("data/synthetic_dataset.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump([{"text": t, "category": c, "is_order": o} for t, c, o in dataset], f, ensure_ascii=False, indent=2)
    logger.info("Synthetic dataset saved to {}", out)
