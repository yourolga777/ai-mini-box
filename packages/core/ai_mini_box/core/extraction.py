import re
from typing import Optional

PHONE_RE = re.compile(r"\+?[\d][\d\s\-\(\)]{5,15}[\d]")


def extract_phone(text: str) -> Optional[str]:
    """Извлекает первый номер телефона из текста."""
    m = PHONE_RE.search(text)
    if m:
        candidate = m.group(0).strip()
        digits = sum(1 for c in candidate if c.isdigit())
        if 7 <= digits <= 15:
            return candidate
    return None
