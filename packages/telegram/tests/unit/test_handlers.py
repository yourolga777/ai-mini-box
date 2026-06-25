import pytest

from ai_mini_box.core.models import Contact, Message, MessageSource, Topic
from ai_mini_box.testing import MockContactRepo, MockMessageRepo, MockKnowledgeBaseRepo

from ai_mini_box_telegram.handlers import process_update


@pytest.fixture
def mock_repos(mocker):
    contact_repo = MockContactRepo()
    message_repo = MockMessageRepo()

    class FakeRepoContainer:
        def __init__(self, session):
            self.contacts = contact_repo
            self.messages = message_repo
            self.kb = MockKnowledgeBaseRepo()

    mocker.patch(
        "ai_mini_box_telegram.handlers.RepoContainer",
        FakeRepoContainer,
    )
    return contact_repo, message_repo


class FakeUpdate:
    @staticmethod
    def text_message(update_id=1, chat_id=123, text="Hello"):
        return {
            "update_id": update_id,
            "message": {
                "chat": {"id": chat_id},
                "text": text,
            },
        }

    @staticmethod
    def no_message(update_id=1):
        return {"update_id": update_id}

    @staticmethod
    def business_message(update_id=1, chat_id=123, text="Business hello"):
        return {
            "update_id": update_id,
            "business_message": {
                "chat": {"id": chat_id},
                "text": text,
                "from": {"first_name": "Biz", "last_name": "User"},
            },
        }


class TestProcessUpdate:
    def test_creates_message_and_contact(self, mock_repos, mocker):
        contact_repo, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message()
        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert len(messages) == 1
        assert messages[0].text == "Hello"
        assert messages[0].source == MessageSource.TELEGRAM
        assert messages[0].chat_id == "123"
        assert messages[0].topic == Topic.OTHER

        contacts = contact_repo.list()
        assert len(contacts) == 1
        assert contacts[0].telegram == "123"

    def test_reuses_existing_contact(self, mock_repos, mocker):
        contact_repo, message_repo = mock_repos
        existing = contact_repo.add(Contact(name="999", telegram="999", source=MessageSource.TELEGRAM))
        session = mocker.Mock()
        update = FakeUpdate.text_message(chat_id=999)
        result = process_update(update, session)

        assert result is True
        contacts = contact_repo.list()
        assert len(contacts) == 1
        assert contacts[0].id == existing.id
        messages = message_repo.list()
        assert len(messages) == 1
        assert messages[0].contact_id == existing.id

    def test_filters_by_allowed_chat_ids(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message(chat_id=999)
        result = process_update(update, session, allowed_chat_ids=[123])

        assert result is False
        assert len(message_repo.list()) == 0

    def test_allows_chat_in_allowed_list(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.text_message(chat_id=123)
        result = process_update(update, session, allowed_chat_ids=[123, 456])

        assert result is True
        assert len(message_repo.list()) == 1

    def test_skips_update_without_message(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.no_message()
        result = process_update(update, session)

        assert result is False
        assert len(message_repo.list()) == 0

    def test_handles_business_message(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.business_message()
        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert len(messages) == 1
        assert messages[0].text == "Business hello"
        assert messages[0].extracted_name == "Biz User"

    def test_handles_business_message_filters_chat(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = FakeUpdate.business_message(chat_id=999)
        result = process_update(update, session, allowed_chat_ids=[123])

        assert result is False
        assert len(message_repo.list()) == 0

    def test_handles_caption_as_text(self, mock_repos, mocker):
        _, message_repo = mock_repos
        session = mocker.Mock()
        update = {
            "update_id": 1,
            "message": {
                "chat": {"id": 123},
                "caption": "Photo caption",
            },
        }
        result = process_update(update, session)

        assert result is True
        messages = message_repo.list()
        assert messages[0].text == "Photo caption"
