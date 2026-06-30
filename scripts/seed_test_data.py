"""Seed test data for flower shop 'Цветочный рай'."""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, "packages/core")
sys.path.insert(0, "packages/llm")

from ai_mini_box.infrastructure.database import init_db, get_session
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import (
    BusinessConfig,
    Contact,
    KnowledgeBaseItem,
    Message,
    MessageSource,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Task,
    TaskPriority,
    Topic,
)
from ai_mini_box.infrastructure.business_config import BusinessConfigManager

# ── helpers ──────────────────────────────────────────────────────────


def _println(msg: str) -> None:
    print(f"  \u2022 {msg}")


def _check_skip(session, model_cls, label: str) -> bool:
    from sqlalchemy import select
    from ai_mini_box.infrastructure.database import Base

    table = model_cls.__tablename__
    result = session.execute(select(model_cls).limit(1)).scalar_one_or_none()
    if result is not None:
        _println(f"{label} already exists \u2014 skipping")
        return True
    return False


# ── data ──────────────────────────────────────────────────────────────

CONTACTS = [
    Contact(
        name="Анна Смирнова",
        phone="+7-901-111-22-33",
        telegram="@anna_flowers",
        source=MessageSource.TELEGRAM,
        notes="Постоянный клиент, любит розы",
    ),
    Contact(
        name="Иван Петров",
        phone="+7-902-222-33-44",
        whatsapp="+7-902-222-33-44",
        source=MessageSource.WHATSAPP,
        notes="Корпоративный клиент, офис на Ленина 15",
    ),
    Contact(
        name="Елена Кузнецова",
        phone="+7-903-333-44-55",
        telegram="@elena_k",
        source=MessageSource.TELEGRAM,
        notes="Заказывает комнатные растения",
    ),
    Contact(
        name="Ольга Новикова",
        phone="+7-904-444-55-66",
        email="olga.novikova@mail.ru",
        source=MessageSource.EMAIL,
    ),
    Contact(
        name="Дмитрий Соколов",
        phone="+7-905-555-66-77",
        telegram="@dmitry_s",
        source=MessageSource.TELEGRAM,
        notes="Часто заказывает букеты на свидания",
    ),
]

PRODUCTS = [
    Product(
        name="Роза красная 60см",
        description="Красная роза, высота 60см, премиум сорт",
        price_kopecks=15000,
        stock=100,
        unit="шт",
        category="Розы",
    ),
    Product(
        name="Роза белая 60см",
        description="Белая роза, высота 60см, премиум сорт",
        price_kopecks=18000,
        stock=80,
        unit="шт",
        category="Розы",
    ),
    Product(
        name="Роза чайная кустовая",
        description="Чайно-гибридная роза в горшке",
        price_kopecks=25000,
        stock=30,
        unit="шт",
        category="Розы",
    ),
    Product(
        name="Букет 'Нежность'",
        description="7 белых роз, гипсофила, упаковка крафт",
        price_kopecks=250000,
        stock=15,
        unit="шт",
        category="Букеты",
    ),
    Product(
        name="Букет 'Страсть'",
        description="15 красных роз, орхидея, дизайнерская упаковка",
        price_kopecks=350000,
        stock=10,
        unit="шт",
        category="Букеты",
    ),
    Product(
        name="Монобукет роз 21 шт",
        description="21 красная роза, атласная лента",
        price_kopecks=450000,
        stock=8,
        unit="шт",
        category="Букеты",
    ),
    Product(
        name="Орхидея фаленопсис",
        description="Белая орхидея в керамическом горшке",
        price_kopecks=120000,
        stock=20,
        unit="шт",
        category="Комнатные",
    ),
    Product(
        name="Горшечная роза",
        description="Миниатюрная роза в горшке, цвет микс",
        price_kopecks=80000,
        stock=25,
        unit="шт",
        category="Комнатные",
    ),
    Product(
        name="Упаковка подарочная",
        description="Прозрачная упаковка с лентой",
        price_kopecks=30000,
        stock=200,
        unit="шт",
        category="Упаковка",
    ),
    Product(
        name="Открытка ручной работы",
        description="Авторская открытка с тёплыми словами",
        price_kopecks=15000,
        stock=50,
        unit="шт",
        category="Открытки",
    ),
]

MESSAGES = [
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=1,
        text="Здравствуйте! Подскажите, сколько стоит букет из 9 красных роз с доставкой?",
        received_at=datetime.now() - timedelta(hours=48),
        topic=Topic.PRICES,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=1,
        text="Хочу заказать доставку на завтра к 10 утра в офис на Ленина 15",
        received_at=datetime.now() - timedelta(hours=36),
        topic=Topic.ORDER,
    ),
    Message(
        source=MessageSource.WHATSAPP,
        contact_id=2,
        text="Добрый день! Мне нужен букет на день рождения коллеги. Что посоветуете?",
        received_at=datetime.now() - timedelta(hours=24),
        topic=Topic.ORDER,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=3,
        text="Добрый день, подскажите, орхидея фаленопсис цветёт сейчас?",
        received_at=datetime.now() - timedelta(hours=12),
        topic=Topic.PRICES,
    ),
    Message(
        source=MessageSource.EMAIL,
        contact_id=4,
        text="Здравствуйте. Вчера заказала букет 'Нежность', но розы привезли уже подвявшие. Очень расстроена.",
        received_at=datetime.now() - timedelta(hours=6),
        topic=Topic.COMPLAINT,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=5,
        text="Ребята, вы лучшие! Девушка в восторге от букета, спасибо! Закажу ещё на следующей неделе",
        received_at=datetime.now() - timedelta(hours=4),
        topic=Topic.OTHER,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=5,
        text="Работаете ли вы в это воскресенье? Хочу заказать букет",
        received_at=datetime.now() - timedelta(hours=3),
        topic=Topic.SCHEDULE,
    ),
    Message(
        source=MessageSource.WHATSAPP,
        contact_id=2,
        text="Можно ли заказать белые розы с доставкой в офис на завтра к 14:00?",
        received_at=datetime.now() - timedelta(hours=2),
        topic=Topic.ORDER,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=1,
        text="Сколько идёт доставка по городу? И бесплатная ли она?",
        received_at=datetime.now() - timedelta(hours=1),
        topic=Topic.PRICES,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=3,
        text="Заказала орхидею неделю назад, начала желтеть. Что делать?",
        received_at=datetime.now() - timedelta(minutes=30),
        topic=Topic.COMPLAINT,
    ),
    Message(
        source=MessageSource.EMAIL,
        contact_id=4,
        text="Есть ли у вас подарочные сертификаты? Хочу подарить подруге",
        received_at=datetime.now() - timedelta(minutes=15),
        topic=Topic.PRICES,
    ),
    Message(
        source=MessageSource.TELEGRAM,
        contact_id=5,
        text="Можете собрать букет в пастельных тонах? Бюджет до 3000",
        received_at=datetime.now() - timedelta(minutes=5),
        topic=Topic.ORDER,
    ),
]

KNOWLEDGE_BASE = [
    KnowledgeBaseItem(
        topic=Topic.PRICES,
        question_keywords=["сколько", "стоит", "цена", "букет", "роза"],
        answer_text="Наши цены: красная роза — 150₽/шт, белая — 180₽/шт. "
        "Букеты от 2500₽ (7 роз в упаковке). Доставка бесплатно от 2000₽.",
    ),
    KnowledgeBaseItem(
        topic=Topic.ORDER,
        question_keywords=["заказать", "доставка", "оформить", "купить"],
        answer_text="Для заказа напишите в чат или позвоните +7-900-123-45-67. "
        "Доставка ежедневно 8:00-21:00. Минимальная сумма заказа 1000₽.",
    ),
    KnowledgeBaseItem(
        topic=Topic.COMPLAINT,
        question_keywords=["вялый", "завял", "желтеет", "брак", "вернуть"],
        answer_text="Приносим извинения за неудобства. Мы заменим букет "
        "или вернём деньги в течение 24 часов. Напишите номер заказа "
        "и приложите фото — мы всё решим.",
    ),
    KnowledgeBaseItem(
        topic=Topic.SCHEDULE,
        question_keywords=["работаете", "часы", "воскресенье", "график"],
        answer_text="Мы работаем ежедневно с 8:00 до 21:00, без выходных. "
        "Заказы принимаем круглосуточно через чат.",
    ),
    KnowledgeBaseItem(
        topic=Topic.PRICES,
        question_keywords=["сертификат", "подарочный", "подарок"],
        answer_text="Да, подарочные сертификаты на любую сумму — от 500₽ до 5000₽. "
        "Срок действия 6 месяцев. Можно заказать с доставкой или забрать в магазине.",
    ),
]

# ── main ──────────────────────────────────────────────────────────────


def seed():
    print("Seeding test data for flower shop...")

    init_db()
    session = get_session()
    repos = RepoContainer(session)

    try:
        # ── 1. Contacts ──
        contact_ids = {}
        existing = repos.contacts.list(limit=1)
        if existing:
            _println("contacts already exist — skipping")
            for c in repos.contacts.list():
                contact_ids[c.name] = c.id
        else:
            for c in CONTACTS:
                created = repos.contacts.add(c)
                contact_ids[c.name] = created.id
                _println(f"contact: {c.name} (id={created.id})")
            session.commit()

        # ── 2. Products ──
        product_ids = {}
        existing = repos.products.list(limit=1)
        if existing:
            _println("products already exist — skipping")
            for p in repos.products.list():
                product_ids[p.name] = p.id
        else:
            for p in PRODUCTS:
                created = repos.products.add(p)
                product_ids[p.name] = created.id
                _println(f"product: {p.name} ({p.price_kopecks / 100:.0f}₽)")
            session.commit()

        # ── 3. Orders ──
        order_ids = {}
        existing = repos.orders.list(limit=1)
        if existing:
            _println("orders already exist — skipping")
            for o in repos.orders.list():
                order_ids[o.id] = o.id
        else:
            if contact_ids:
                order_data = [
                    Order(
                        contact_id=contact_ids["Анна Смирнова"],
                        status=OrderStatus.NEW,
                        notes="2 красные розы + упаковка — доставка завтра 10:00",
                    ),
                    Order(
                        contact_id=contact_ids["Иван Петров"],
                        status=OrderStatus.COMPLETED,
                        total_kopecks=365000,
                        notes="Букет 'Страсть' + открытка — доставлено 25.06",
                    ),
                    Order(
                        contact_id=contact_ids["Елена Кузнецова"],
                        status=OrderStatus.PROCESSING,
                        notes="Орхидея фаленопсис + упаковка — собираем",
                    ),
                ]
                for o in order_data:
                    created = repos.orders.add(o)
                    order_ids[created.id] = created.id
                    _println(f"order #{created.id}: {o.status.value} ({o.notes[:50]}...)")
                session.commit()

        # ── 4. Order Items ──
        existing = repos.order_items.list_by_order(list(order_ids)[0]) if order_ids else []
        if existing:
            _println("order_items already exist — skipping")
        else:
            if len(order_ids) >= 3 and product_ids:
                order_list = list(order_ids.keys())
                items = [
                    OrderItem(
                        order_id=order_list[0],
                        product_id=product_ids["Роза красная 60см"],
                        product_name="Роза красная 60см",
                        quantity=2,
                        price_kopecks=15000,
                    ),
                    OrderItem(
                        order_id=order_list[0],
                        product_id=product_ids["Упаковка подарочная"],
                        product_name="Упаковка подарочная",
                        quantity=1,
                        price_kopecks=30000,
                    ),
                    OrderItem(
                        order_id=order_list[1],
                        product_id=product_ids["Букет 'Страсть'"],
                        product_name="Букет 'Страсть'",
                        quantity=1,
                        price_kopecks=350000,
                    ),
                    OrderItem(
                        order_id=order_list[1],
                        product_id=product_ids["Открытка ручной работы"],
                        product_name="Открытка ручной работы",
                        quantity=1,
                        price_kopecks=15000,
                    ),
                    OrderItem(
                        order_id=order_list[2],
                        product_id=product_ids["Орхидея фаленопсис"],
                        product_name="Орхидея фаленопсис",
                        quantity=1,
                        price_kopecks=120000,
                    ),
                    OrderItem(
                        order_id=order_list[2],
                        product_id=product_ids["Упаковка подарочная"],
                        product_name="Упаковка подарочная",
                        quantity=1,
                        price_kopecks=30000,
                    ),
                ]
                for item in items:
                    repos.order_items.add(item)
                session.commit()
                _println(f"order_items: {len(items)} items added")

        # ── 5. Messages ──
        existing = repos.messages.list(limit=1)
        if existing:
            _println("messages already exist — skipping")
        else:
            msg_ids = {}
            for m in MESSAGES:
                created = repos.messages.add(m)
                msg_ids[created.id] = created.id
            session.commit()
            _println(f"messages: {len(MESSAGES)} added")

        # ── 6. Tasks ──
        existing = repos.tasks.list(limit=1)
        if existing:
            _println("tasks already exist — skipping")
        else:
            if contact_ids:
                task_data = [
                    Task(
                        title="Перезвонить Анне Смирновой по поводу повторного заказа",
                        description="Анна заказывала 2 розы, предложить букет со скидкой",
                        due_date=date.today() + timedelta(days=1),
                        due_time="12:00",
                        priority=TaskPriority.MEDIUM,
                        contact_id=contact_ids["Анна Смирнова"],
                    ),
                    Task(
                        title="Проверить статус доставки букета Ивану Петрову",
                        description="Уточнить у курьера, вручён ли букет",
                        due_date=date.today(),
                        due_time="18:00",
                        priority=TaskPriority.HIGH,
                        contact_id=contact_ids["Иван Петров"],
                    ),
                    Task(
                        title="Связаться с Еленой по гарантии на орхидею",
                        description="Клиентка жалуется на пожелтение листьев — предложить замену",
                        due_date=date.today() + timedelta(days=2),
                        due_time="10:00",
                        priority=TaskPriority.LOW,
                        contact_id=contact_ids["Елена Кузнецова"],
                    ),
                ]
                for t in task_data:
                    repos.tasks.add(t)
                session.commit()
                _println(f"tasks: {len(task_data)} added")

        # ── 7. Knowledge Base ──
        existing = repos.kb.list(limit=1)
        if existing:
            _println("knowledge_base already exists — skipping")
        else:
            for kb in KNOWLEDGE_BASE:
                repos.kb.add(kb)
            session.commit()
            _println(f"knowledge_base: {len(KNOWLEDGE_BASE)} entries added")

        # ── 8. Business Config ──
        bm = BusinessConfigManager()
        cfg = bm.load()
        if cfg.company_name != "Цветочный рай":
            cfg.company_name = "Цветочный рай"
            cfg.work_hours = "Пн-Вс 8:00-21:00"
            cfg.delivery_info = (
                "По городу — бесплатно от 2000₽, до 2000₽ — 300₽. "
                "За МКАД — рассчитывается индивидуально."
            )
            cfg.return_policy = (
                "Растения и букеты можно заменить в течение 24 часов "
                "при наличии чека. Живые цветы — только замена."
            )
            cfg.payment_methods = "Наличные, карты (Visa/Mastercard/Мир), перевод на карту СБП"
            cfg.contacts = "Тел: +7-900-123-45-67, чат в Telegram @flowers_bot, email: info@cvetochniy-ray.ru"
            cfg.faq = [
                {"question": "Как долго стоят розы в вазе?", "answer": "При правильном уходе розы стоят 7-10 дней. " "Рекомендуем подрезать стебель каждые 2 дня и менять воду."},
                {"question": "Есть ли доставка ночью?", "answer": "Доставка работает с 8:00 до 21:00. " "Ночная доставка возможна по предзаказу (минимум за 24 часа) с доплатой 500₽."},
                {"question": "Можно ли вернуть букет?", "answer": "Живые цветы обмену и возврату не подлежат, " "но мы заменим букет, если качество вас не устроило, в течение 24 часов."},
            ]
            bm.save(cfg)
            _println("business_config updated: 'Цветочный рай'")
        else:
            _println("business_config already set — skipping")

        print(f"\n{'='*50}")
        print("Seed complete. Summary:")
        print(f"  Contacts: {len(repos.contacts.list())}")
        print(f"  Products: {len(repos.products.list())}")
        print(f"  Orders:   {len(repos.orders.list())}")
        print(f"  Messages: {len(repos.messages.list())}")
        print(f"  Tasks:    {len(repos.tasks.list())}")
        print(f"  KB:       {len(repos.kb.list())}")
        print(f"{'='*50}")

    except Exception as e:
        session.rollback()
        print(f"  ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
