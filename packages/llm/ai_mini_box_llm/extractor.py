from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

PHONE_RE = re.compile(r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}")
DATE_RE = re.compile(
    r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?"
    r"|(завтра|сегодня|послезавтра|через\s+\d+\s+(?:день|дня|дней|недел[юяи]|месяц[а]?))"
)
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(?:утра|дня|вечера)?")
ADDRESS_RE = re.compile(
    r"(?:ул\.?|улица|пр\.?|проспект|д\.?|дом|кв\.?|квартира)\s*[а-яА-Я0-9\s.-]+"
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
NAME_RE = re.compile(
    r"(?:меня\s+зовут|я\s+[\w]+|клиент|покупател[ья])\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)"
)

ORDER_ITEM_RE = re.compile(
    r"(\d+)\s*(?:шт\.?|штук[аи]?|единиц[аы]?)?\s*(.+?)(?:\s+по\s+(\d+))?\s*(?:руб|₽|р\.)?"
    r"|(?:зака(?:зать|живаю)|нужно|требуется|купить|пришлите)\s+(\d+)\s*(?:шт\.?|штук[аи]?)?\s*(.+?)$"
)

NORMALIZE_MAP: dict[str, str] = {
    "прив": "привет",
    "здрасте": "здравствуйте",
    "спс": "спасибо",
    "щас": "сейчас",
    "мб": "может быть",
    "пж": "пожалуйста",
    "плз": "пожалуйста",
    "норм": "нормально",
    "ок": "хорошо",
}


class EntityExtractor:
    def normalize(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        for slang, literal in NORMALIZE_MAP.items():
            text = re.sub(rf"\b{re.escape(slang)}\b", literal, text, flags=re.IGNORECASE)
        text = re.sub(r"([а-яА-Я])\1{2,}", r"\1\1", text)
        return text

    def extract(self, text: str) -> dict[str, Any]:
        if not text:
            return {}
        result: dict[str, Any] = {}

        phone_match = PHONE_RE.search(text)
        if phone_match:
            result["phone"] = phone_match.group(0).strip()

        date_match = DATE_RE.search(text)
        if date_match:
            parsed = self._parse_date(date_match)
            if parsed:
                result["date"] = parsed

        time_match = TIME_RE.search(text)
        if time_match:
            h, m = time_match.group(1), time_match.group(2)
            result["time"] = f"{h}:{m}"

        addr_match = ADDRESS_RE.search(text)
        if addr_match:
            result["address"] = addr_match.group(0).strip()

        email_match = EMAIL_RE.search(text)
        if email_match:
            result["email"] = email_match.group(0).strip()

        name_match = NAME_RE.search(text)
        if name_match:
            result["name"] = name_match.group(1).strip()

        return result

    def extract_order_items(self, text: str) -> list[dict[str, Any]]:
        if not text:
            return []
        items: list[dict[str, Any]] = []
        for match in ORDER_ITEM_RE.finditer(text):
            if match.group(1) and match.group(2):
                qty = int(match.group(1))
                product = match.group(2).strip().rstrip(".,!?")
                price = int(match.group(3)) if match.group(3) else 0
                items.append({"product": product, "quantity": qty, "price": price})
            elif match.group(5) and match.group(6):
                qty = int(match.group(5)) if match.group(5) else 1
                product = match.group(6).strip().rstrip(".,!?")
                items.append({"product": product, "quantity": qty, "price": 0})
        return items

    def has_product_keywords(self, text: str) -> bool:
        if not text:
            return False
        keywords = [
            r"\bкупить\b", r"\bзаказать\b", r"\bзакажу\b", r"\bзаказываю\b",
            r"\bнужно\b", r"\bтребуется\b", r"\bпришлите\b",
            r"\bхочу\b.*\b(?:заказать|купить)\b",
            r"\b\d+\s*(?:шт|штук)",
        ]
        return any(re.search(kw, text, re.IGNORECASE) for kw in keywords)

    def _parse_date(self, match: re.Match) -> str | None:
        if match.group(4):
            relative = match.group(4).lower()
            today = date.today()
            if "завтра" in relative:
                return (today + timedelta(days=1)).isoformat()
            if "сегодня" in relative:
                return today.isoformat()
            if "послезавтра" in relative:
                return (today + timedelta(days=2)).isoformat()
            if "через" in relative:
                num_match = re.search(r"(\d+)", relative)
                if num_match:
                    num = int(num_match.group(1))
                    if "дн" in relative:
                        return (today + timedelta(days=num)).isoformat()
                    if "недел" in relative:
                        return (today + timedelta(weeks=num)).isoformat()
                    if "месяц" in relative:
                        return (today.replace(month=today.month + num) if today.month + num <= 12 else today).isoformat()
            return None
        d, m, y = match.group(1), match.group(2), match.group(3)
        day, month = int(d), int(m)
        year = int(y) if y else date.today().year
        if year < 100:
            year += 2000
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
