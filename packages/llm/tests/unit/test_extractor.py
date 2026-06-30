from __future__ import annotations

from ai_mini_box_llm.extractor import EntityExtractor


class TestEntityExtractor:
    def setup_method(self):
        self.ext = EntityExtractor()

    def test_extract_phone(self):
        result = self.ext.extract("+7 999 123-45-67")
        assert result["phone"] == "+7 999 123-45-67"

    def test_extract_phone_without_spaces(self):
        result = self.ext.extract("+79991234567")
        assert result["phone"] == "+79991234567"

    def test_extract_phone_8(self):
        result = self.ext.extract("8 (999) 123-45-67")
        assert "phone" in result

    def test_extract_date_dmy(self):
        result = self.ext.extract("встреча 15.06.2026")
        assert result.get("date") == "2026-06-15"

    def test_extract_date_relative_tomorrow(self):
        result = self.ext.extract("завтра в 15:00")
        assert "date" in result
        assert "time" in result
        assert result["time"] == "15:00"

    def test_extract_address(self):
        result = self.ext.extract("ул. Ленина, д. 10, кв. 5")
        assert "address" in result

    def test_extract_email(self):
        result = self.ext.extract("пишите на test@example.com")
        assert result["email"] == "test@example.com"

    def test_extract_name(self):
        result = self.ext.extract("меня зовут Иван Петров")
        assert result.get("name") == "Иван Петров"

    def test_empty_text(self):
        assert self.ext.extract("") == {}

    def test_no_entities(self):
        result = self.ext.extract("нормально, спасибо")
        assert result == {}

    def test_normalize_slang(self):
        result = self.ext.normalize("прив, спс")
        assert "привет" in result
        assert "спасибо" in result

    def test_normalize_empty(self):
        assert self.ext.normalize("") == ""

    def test_has_product_keywords(self):
        assert self.ext.has_product_keywords("хочу заказать пиццу")
        assert self.ext.has_product_keywords("нужно 5 ноутбуков")
        assert not self.ext.has_product_keywords("спасибо, всё хорошо")

    def test_extract_order_items(self):
        items = self.ext.extract_order_items("2 ноутбука Lenovo")
        assert len(items) > 0
        if items:
            assert "product" in items[0]
            assert "quantity" in items[0]
