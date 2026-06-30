import pytest

from ai_mini_box.core.models import Contact, Message, MessageSource, Topic
from ai_mini_box.testing import MockContactRepo, MockMessageRepo, MockOrderRepo

from ai_mini_box_telegram.handlers import _category_to_topic, get_chat_history, process_update


@pytest.fixture
def mock_repos(mocker):
    contact_repo = MockContactRepo()
    message_repo = MockMessageRepo()
    order_repo = MockOrderRepo()

    class FakeRepoContainer:
        def __init__(self, session):
            self.contacts = contact_repo
            self.messages = message_repo
            self.orders = order_repo
            self.kb = mocker.Mock()

    mocker.patch(
        "ai_mini_box_telegram.handlers.RepoContainer",
        FakeRepoContainer,
    )
    return contact_repo, message_repo, order_repo


class FakeUpdate:
    @staticmethod
    def text_message(update_id=1, chat_id=123, text="Hello"):
        return {
            "update_id": update_id,
            "message": {
                "chat": {"id": chat_id},
                "from": {"first_name": "Test", "last_name": "User"},
                "text": text,
            },
        }

    @staticmethod
    def no_message(update_id=1):
        return {"update_id": update_id}


class TestCategoryToTopic:
    def test_maps_order(self):
        assert _category_to_topic("ЗАКАЗ") == Topic.ORDER

    def test_maps_complaint(self):
        assert _category_to_topic("ЖАЛОБА") == Topic.COMPLAINT

    def test_maps_other(self):
        assert _category_to_topic("ФЛУД") == Topic.OTHER

    def test_unknown_category_returns_none(self):
        assert _category_to_topic("ВОПРОС") is None
        assert _category_to_topic("ПРЕДЛОЖЕНИЕ") is None
        assert _category_to_topic("anything") is None


class TestGetChatHistory:
    def test_returns_empty_when_no_messages(self, mock_repos):
        _, message_repo, _ = mock_repos
        repos = type("R", (), {"messages": message_repo})()
        history = get_chat_history(repos, "123")
        assert history == []

    def test_returns_user_messages(self, mock_repos):
        _, message_repo, _ = mock_repos
        message_repo.add(Message(text="Hello", chat_id="123", source=MessageSource.TELEGRAM))
        repos = type("R", (), {"messages": message_repo})()
        history = get_chat_history(repos, "123")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["text"] == "Hello"

    def test_returns_assistant_messages(self, mock_repos):
        _, message_repo, _ = mock_repos
        message_repo.add(Message(
            text="Hello",
            chat_id="123",
            source=MessageSource.TELEGRAM,
            sent_response=True,
            auto_reply_text="Auto reply",
        ))
        repos = type("R", (), {"messages": message_repo})()
        history = get_chat_history(repos, "123")
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["text"] == "Auto reply"

    def test_returns_last_5_messages(self, mock_repos):
        _, message_repo, _ = mock_repos
        for i in range(10):
            message_repo.add(Message(
                text=f"Message {i}", chat_id="123", source=MessageSource.TELEGRAM,
            ))
        repos = type("R", (), {"messages": message_repo})()
        history = get_chat_history(repos, "123", limit=5)
        assert len(history) == 5


class TestProcessUpdatePipeline:
    def test_saves_message_without_pipeline(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            return_value=None,
        )

        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert len(messages) == 1
        assert messages[0].text == "Hello"
        assert messages[0].topic is None

    def test_saves_message_when_pipeline_fails(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.side_effect = ValueError("Pipeline error")
        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            return_value=mock_pipeline,
        )

        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert len(messages) == 1

    def test_enriches_message_from_pipeline(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mock_result = mocker.Mock()
        mock_result.category = "ЗАКАЗ"
        mock_result.confidence = 0.95
        mock_result.need_human = False
        mock_result.reply_text = "Ваш заказ принят"
        mock_result.is_order = False

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.return_value = mock_result
        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            return_value=mock_pipeline,
        )

        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert len(messages) == 1
        msg = messages[0]
        assert msg.category == "ЗАКАЗ"
        assert msg.need_human is False
        assert msg.auto_replied is True
        assert msg.auto_reply_text == "Ваш заказ принят"
        assert msg.topic == Topic.ORDER
        assert msg.subcategory is None

    def test_auto_reply_not_sent_when_need_human(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mock_result = mocker.Mock()
        mock_result.category = "ЖАЛОБА"
        mock_result.confidence = 0.5
        mock_result.need_human = True
        mock_result.reply_text = "Жалоба зарегистрирована"
        mock_result.is_order = False

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.return_value = mock_result
        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            return_value=mock_pipeline,
        )

        mock_tg = mocker.Mock()
        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            side_effect=lambda name: mock_tg if name == "telegram" else mock_pipeline,
        )

        result = process_update(update, session)

        assert result is True
        mock_tg.send_message.assert_not_called()

    def test_auto_reply_sent_when_not_need_human(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mock_result = mocker.Mock()
        mock_result.category = "ЗАКАЗ"
        mock_result.confidence = 0.95
        mock_result.need_human = False
        mock_result.reply_text = "Ваш заказ принят"
        mock_result.is_order = False

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.return_value = mock_result

        mock_tg = mocker.Mock()

        def _get_service(name):
            if name == "telegram":
                return mock_tg
            return mock_pipeline

        mocker.patch("ai_mini_box_telegram.handlers.get_service", _get_service)

        result = process_update(update, session)

        assert result is True
        mock_tg.send_message.assert_called_once()

    def test_creates_order_when_is_order(self, mock_repos, mocker):
        _, message_repo, order_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message(text="Хочу пиццу")

        mock_result = mocker.Mock()
        mock_result.category = "ЗАКАЗ"
        mock_result.confidence = 0.95
        mock_result.need_human = False
        mock_result.reply_text = "Заказ создан"
        mock_result.is_order = True

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.return_value = mock_result

        mock_tg = mocker.Mock()

        def _get_service(name):
            if name == "telegram":
                return mock_tg
            return mock_pipeline

        mocker.patch("ai_mini_box_telegram.handlers.get_service", _get_service)

        result = process_update(update, session)

        assert result is True
        orders = order_repo.list()
        assert len(orders) == 1
        assert orders[0].notes == "Хочу пиццу"

    def test_does_not_create_order_when_not_is_order(self, mock_repos, mocker):
        _, message_repo, order_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()

        mock_result = mocker.Mock()
        mock_result.category = "ВОПРОС"
        mock_result.confidence = 0.8
        mock_result.need_human = True
        mock_result.reply_text = None
        mock_result.is_order = False

        mock_pipeline = mocker.Mock()
        mock_pipeline.process.return_value = mock_result
        mocker.patch(
            "ai_mini_box_telegram.handlers.get_service",
            return_value=mock_pipeline,
        )

        result = process_update(update, session)

        assert result is True
        orders = order_repo.list()
        assert len(orders) == 0

    def test_filters_by_allowed_chat_ids(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message(chat_id=999)
        result = process_update(update, session, allowed_chat_ids=[123])

        assert result is False
        assert len(message_repo.list()) == 0

    def test_skips_update_without_message(self, mock_repos, mocker):
        _, message_repo, _ = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.no_message()
        result = process_update(update, session)

        assert result is False
        assert len(message_repo.list()) == 0
