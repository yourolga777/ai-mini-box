from pathlib import Path

from ai_mini_box_telegram.state import (
    FileTelegramStateRepo,
    MemoryTelegramStateRepo,
    TelegramStateRepo,
)


class TestMemoryTelegramStateRepo:
    def test_initial_offset_is_none(self):
        repo = MemoryTelegramStateRepo()
        assert repo.get_offset() is None

    def test_save_and_get_offset(self):
        repo = MemoryTelegramStateRepo()
        repo.save_offset(42)
        assert repo.get_offset() == 42

    def test_overwrites_offset(self):
        repo = MemoryTelegramStateRepo()
        repo.save_offset(1)
        repo.save_offset(999)
        assert repo.get_offset() == 999

    def test_is_telegram_state_repo(self):
        assert isinstance(MemoryTelegramStateRepo(), TelegramStateRepo)


class TestFileTelegramStateRepo:
    def test_initial_offset_is_none_when_file_missing(self, tmp_path: Path):
        repo = FileTelegramStateRepo(str(tmp_path / "state.json"))
        assert repo.get_offset() is None

    def test_save_and_get_offset(self, tmp_path: Path):
        path = str(tmp_path / "state.json")
        repo = FileTelegramStateRepo(path)
        repo.save_offset(42)
        assert repo.get_offset() == 42

    def test_overwrites_offset(self, tmp_path: Path):
        path = str(tmp_path / "state.json")
        repo = FileTelegramStateRepo(path)
        repo.save_offset(1)
        repo.save_offset(777)
        assert repo.get_offset() == 777

    def test_returns_none_on_corrupted_json(self, tmp_path: Path):
        state_file = tmp_path / "state.json"
        state_file.write_text("{invalid", encoding="utf-8")
        repo = FileTelegramStateRepo(str(state_file))
        assert repo.get_offset() is None

    def test_returns_none_on_empty_file(self, tmp_path: Path):
        state_file = tmp_path / "state.json"
        state_file.write_text("", encoding="utf-8")
        repo = FileTelegramStateRepo(str(state_file))
        assert repo.get_offset() is None

    def test_returns_none_on_non_int_offset(self, tmp_path: Path):
        state_file = tmp_path / "state.json"
        state_file.write_text('{"offset": "not_an_int"}', encoding="utf-8")
        repo = FileTelegramStateRepo(str(state_file))
        assert repo.get_offset() is None

    def test_atomic_write_preserves_data(self, tmp_path: Path):
        path = str(tmp_path / "state.json")
        repo = FileTelegramStateRepo(path)
        repo.save_offset(42)
        assert repo.get_offset() == 42
        repo.save_offset(99)
        assert repo.get_offset() == 99

    def test_is_telegram_state_repo(self):
        assert isinstance(FileTelegramStateRepo(), TelegramStateRepo)
