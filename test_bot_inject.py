"""Test script: inject 10 fake Telegram updates and verify classification."""

from ai_mini_box.infrastructure.database import init_db, get_db, dispose_engine
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Topic
from ai_mini_box_telegram.handlers import process_update

UPDATES = [
    (1, 100, "Сколько стоит доставка?", Topic.PRICES),
    (2, 100, "Хочу заказать 5 кг яблок", Topic.ORDER),
    (3, 100, "Товар пришёл бракованный", Topic.COMPLAINT),
    (4, 100, "Во сколько открываетесь?", Topic.SCHEDULE),
    (5, 100, "Привет, как дела?", Topic.OTHER),
    (6, 100, "Есть скидка на опт?", Topic.PRICES),
    (7, 100, "Оформите пожалуйста заказ", Topic.ORDER),
    (8, 100, "У меня проблема с оплатой", Topic.COMPLAINT),
    (9, 100, "Работаете в субботу?", Topic.SCHEDULE),
    (10, 100, "Спасибо за работу", Topic.OTHER),
]


def make_update(update_id, chat_id, text):
    return {
        "update_id": update_id,
        "message": {
            "chat": {"id": chat_id},
            "text": text,
        },
    }


def main():
    init_db()

    results = []
    for update_id, chat_id, text, expected_topic in UPDATES:
        update = make_update(update_id, chat_id, text)
        with get_db() as session:
            ok = process_update(update, session)
            if ok:
                repos = RepoContainer(session)
                msgs = repos.messages.list(limit=50, sort="update_id")
                last = msgs[-1] if msgs else None
                actual_topic = last.topic if last else None
            else:
                actual_topic = None
        results.append((update_id, text, expected_topic, actual_topic, actual_topic == expected_topic))

    print(f"{'ID':<5} {'Text':<35} {'Expected':<15} {'Actual':<15} {'Status':<5}")
    print("-" * 75)
    for update_id, text, expected, actual, passed in results:
        actual_val = actual.value if actual else "N/A"
        expected_val = expected.value if expected else "N/A"
        status = "+" if passed else "-"
        print(f"{update_id:<5} {text:<35} {expected_val:<15} {actual_val:<15} {status:<5}")

    correct = sum(1 for r in results if r[4])
    total = len(results)
    print(f"\n{correct}/{total} — correct topic classification")
    print("ALL PASSED" if correct == total else f"FAILURES: {total - correct}")

    dispose_engine()


if __name__ == "__main__":
    main()
