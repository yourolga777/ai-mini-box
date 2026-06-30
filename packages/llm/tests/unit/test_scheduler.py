from unittest.mock import MagicMock, patch

from ai_mini_box.core.services.registry import register_service


def test_scheduler_initialization():
    """TaskScheduler init does not crash with valid db_url."""
    from ai_mini_box_llm.scheduler import TaskScheduler

    s = TaskScheduler("sqlite:///:memory:")
    assert s._scheduler is not None


def test_scheduler_setup_registers_four_jobs():
    """setup() adds all 4 scheduled jobs."""
    from ai_mini_box_llm.scheduler import TaskScheduler

    s = TaskScheduler("sqlite:///:memory:")
    s.setup()
    jobs = s._scheduler.get_jobs()
    job_ids = [j.id for j in jobs]
    assert "nightly_retrain" in job_ids
    assert "sync_templates" in job_ids
    assert "rebuild_rag_index" in job_ids
    assert "cleanup_logs" in job_ids
    s.shutdown()


def test_scheduler_shutdown_does_not_crash():
    """shutdown() gracefully handles already-stopped scheduler."""
    from ai_mini_box_llm.scheduler import TaskScheduler

    s = TaskScheduler("sqlite:///:memory:")
    s.shutdown()


def test_nightly_retrain_no_trainer_does_not_crash():
    """_job_nightly_retrain handles missing trainer gracefully."""
    from ai_mini_box_llm.scheduler import _job_nightly_retrain

    register_service("trainer", None)
    _job_nightly_retrain()


def test_sync_templates_no_sync_does_not_crash():
    """_job_sync_templates handles missing service gracefully."""
    from ai_mini_box_llm.scheduler import _job_sync_templates

    register_service("system_template_sync", None)
    _job_sync_templates()


def test_rebuild_rag_index_no_pipeline_does_not_crash():
    """_job_rebuild_rag_index handles missing pipeline gracefully."""
    from ai_mini_box_llm.scheduler import _job_rebuild_rag_index

    register_service("llm", None)
    _job_rebuild_rag_index()


def test_nightly_retrain_calls_trainer():
    """_job_nightly_retrain calls trainer.nightly_retrain()."""
    from ai_mini_box_llm.scheduler import _job_nightly_retrain

    trainer = MagicMock()
    trainer.nightly_retrain.return_value = {"accuracy": 0.85}
    register_service("trainer", trainer)

    _job_nightly_retrain()
    trainer.nightly_retrain.assert_called_once()


def test_sync_templates_calls_sync():
    """_job_sync_templates calls sync_on_startup()."""
    from ai_mini_box_llm.scheduler import _job_sync_templates

    sync = MagicMock()
    register_service("system_template_sync", sync)

    _job_sync_templates()
    sync.sync_on_startup.assert_called_once()
