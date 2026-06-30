from __future__ import annotations

import atexit
import json
from typing import Optional

import typer
from loguru import logger
from sqlalchemy import select

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.services.registry import register_service, get_service

from .auto_processor import AutoProcessor
from .cache import ResponseCache
from .classifier import ClassifierEnsemble
from .config import LlmConfig
from .extractor import EntityExtractor
from .monitoring import DriftMonitor
from .pipeline import Pipeline
from .rag.embeddings import EmbeddingModel
from .rag.retriever import Retriever
from .rag.vector_store import FaissVectorStore
from .scheduler import TaskScheduler
from .training import Trainer

logger.add("logs/plugin_llm.log", rotation="1 MB", retention=3)

SYSTEM_CATEGORIES = [
    {"name": "Цены", "description": "Вопросы о ценах, скидках, оплате", "color": "#16a34a"},
    {"name": "Заказ", "description": "Оформление заказа, покупка, статус доставки", "color": "#2563eb"},
    {"name": "Жалоба", "description": "Жалобы, проблемы, возврат, брак", "color": "#dc2626"},
    {"name": "График", "description": "Часы работы, расписание", "color": "#ca8a04"},
    {"name": "Другое", "description": "Всё остальное", "color": "#6b7280"},
]


def _ensure_tables() -> None:
    from ai_mini_box.infrastructure.database import Base, get_engine

    import ai_mini_box.infrastructure.orm_models  # noqa: F401
    import ai_mini_box_llm.models  # noqa: F401

    Base.metadata.create_all(get_engine())
    logger.debug("LLM plugin tables ensured")


def _seed_system_categories() -> None:
    from ai_mini_box.infrastructure.database import get_db
    from .models import MessageCategory

    with get_db() as session:
        existing = session.execute(select(MessageCategory).limit(1)).scalar_one_or_none()
        if existing is not None:
            return
        for data in SYSTEM_CATEGORIES:
            session.add(MessageCategory(**data, is_system=True))
        logger.info("Seeded {} system categories", len(SYSTEM_CATEGORIES))


_GLOBAL_PIPELINE: Pipeline | None = None


def _init_pipeline() -> Pipeline | None:
    global _GLOBAL_PIPELINE
    if _GLOBAL_PIPELINE is not None:
        return _GLOBAL_PIPELINE

    classifier = ClassifierEnsemble()
    if not classifier.load():
        logger.info("No pre-trained classifier found — generating synthetic data")
        try:
            from .scripts.generate_synthetic import generate_and_train
            generate_and_train(classifier)
        except Exception as e:
            logger.warning("Synthetic data generation failed: {}", e)

    extractor = EntityExtractor()

    embed_model = EmbeddingModel()
    vector_store = FaissVectorStore()
    vector_store.load()
    retriever = Retriever(embed_model, vector_store)

    from ai_mini_box.infrastructure.database import get_db
    from .templates.store import TemplateStore

    template_store = TemplateStore(get_db)
    cache = ResponseCache()
    pipeline = Pipeline(classifier, extractor, template_store, retriever, cache)
    _GLOBAL_PIPELINE = pipeline
    return pipeline


def _get_pipeline() -> Pipeline:
    p = _init_pipeline()
    if p is None:
        raise RuntimeError("Pipeline not initialized")
    return p


def config_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "provider": {"type": "string", "title": "Провайдер (зарезервировано)", "enum": ["local", "remote"], "default": "local"},
            "rag_enabled": {"type": "boolean", "title": "RAG включён", "default": False},
            "rag_top_k": {"type": "integer", "title": "RAG top-K", "default": 3},
        },
        "required": [],
    }


def register(app: typer.Typer) -> None:
    _ensure_tables()
    _seed_system_categories()

    from ai_mini_box.infrastructure.database import get_db, get_db_url, get_engine

    _scheduler: TaskScheduler | None = None
    try:
        _scheduler = TaskScheduler(engine=get_engine())

        pipeline = _init_pipeline()
        register_service("llm", pipeline)
        logger.info("LLM pipeline registered")

        trainer = Trainer(pipeline._classifier, lambda: _get_db_safe())
        register_service("trainer", trainer)

        monitor = DriftMonitor(lambda: _get_db_safe())
        register_service("drift_monitor", monitor)

        register_service("auto_processor", AutoProcessor())
        logger.info("AutoProcessor registered")

        from .templates.sync import SystemTemplateSync
        system_sync = SystemTemplateSync(get_db)
        register_service("system_template_sync", system_sync)
        system_sync.sync_on_startup()

        _scheduler.setup()
        logger.info("LLM scheduler started")
    except Exception as e:
        logger.warning("LLM plugin skipped: {}", e)
    finally:
        if _scheduler:
            atexit.register(_scheduler.shutdown)

    llm_app = typer.Typer(help="LLM commands")
    app.add_typer(llm_app, name="llm")

    @llm_app.command()
    def status():
        """Show LLM pipeline status."""
        try:
            pipeline = _get_pipeline()
            cfg = LlmConfig.load()
            model_path = cfg.model_path or "N/A (synthetic classifier)"
            typer.echo(f"Classifier:    {'fitted' if pipeline._classifier._fitted else 'cold start'}")
            typer.echo(f"RAG:           {'enabled' if pipeline._rag.available else 'disabled'}")
            typer.echo(f"Cache:         {pipeline._cache.stats()['size']} entries")
            typer.echo("Status:       active")
        except Exception:
            typer.echo("LLM: not active")

    @llm_app.command()
    def classify(
        text: str = typer.Argument(..., help="Message text to classify"),
    ):
        """Classify a message category."""
        try:
            pipeline = _get_pipeline()
        except Exception:
            typer.echo("Error: LLM pipeline is not active.")
            raise typer.Exit(1)
        category, confidence = pipeline._classifier.predict(text)
        typer.echo(f"Category:  {category}")
        typer.echo(f"Confidence: {confidence:.1%}")

    @llm_app.command()
    def draft(
        text: str = typer.Argument(..., help="Message text"),
    ):
        """Generate a draft response via pipeline."""
        try:
            pipeline = _get_pipeline()
        except Exception:
            typer.echo("Error: LLM pipeline is not active.")
            raise typer.Exit(1)
        result = pipeline.process(text)
        if result.reply_text:
            typer.echo(result.reply_text)
        else:
            typer.echo("No draft available.")

    @llm_app.command()
    def extract(
        text: str = typer.Argument(..., help="Message text"),
    ):
        """Extract entities from text."""
        try:
            pipeline = _get_pipeline()
        except Exception:
            typer.echo("Error: LLM pipeline is not active.")
            raise typer.Exit(1)
        entities = pipeline._extractor.extract(text)
        typer.echo(json.dumps(entities, ensure_ascii=False, indent=2))

    @llm_app.command()
    def retrain():
        """Manual classifier retrain."""
        trainer = get_service("trainer")
        if trainer is None:
            typer.echo("Trainer not available")
            raise typer.Exit(1)
        metrics = trainer.auto_train()
        typer.echo(f"Retrained. Accuracy: {metrics.get('accuracy', 0):.1%}")

    @llm_app.command()
    def generate_synthetic(
        count: int = typer.Option(500, "--count", "-n", help="Number of samples"),
    ):
        """Generate synthetic training data."""
        try:
            pipeline = _get_pipeline()
        except Exception:
            typer.echo("Error: LLM pipeline is not active.")
            raise typer.Exit(1)
        from .scripts.generate_synthetic import generate_and_train
        generate_and_train(pipeline._classifier)
        typer.echo(f"Generated and trained on {count} synthetic samples.")

    @llm_app.command()
    def accuracy():
        """Show classifier accuracy for last 7 days."""
        monitor = get_service("drift_monitor")
        if monitor is None:
            typer.echo("Drift monitor not available")
            raise typer.Exit(1)
        acc = monitor.compute_accuracy()
        typer.echo(f"7-day accuracy: {acc:.1%}")

    @llm_app.command()
    def assign_all(
        limit: int = typer.Option(50, "--limit", "-n", help="Max messages (0 = all)"),
    ):
        """Assign folders to messages without a folder."""
        try:
            _get_pipeline()
        except Exception:
            typer.echo("LLM pipeline not configured")
            raise typer.Exit(code=0)

        processor = AutoProcessor()
        total, assigned = processor.process_all(limit=limit)
        typer.echo(f"Checked {total} messages, assigned {assigned} to folders")

    @llm_app.command()
    def process_daemon(
        interval: int = typer.Option(60, "--interval", "-i", help="Пауза между циклами (сек)"),
    ):
        """Daemon: бесконечный цикл обработки сообщений через AutoProcessor."""
        from .daemon import run_daemon
        run_daemon(interval=interval)

    @llm_app.command()
    def daemon(
        interval: int = typer.Option(60, "--interval", "-i", help="Пауза между циклами (сек)"),
    ):
        """Run LLM processing daemon (alias for process-daemon, used by PluginManager)."""
        from .daemon import run_daemon
        run_daemon(interval=interval)

    folder_app = typer.Typer(help="Manage message folders/categories")
    llm_app.add_typer(folder_app, name="folder")

    @folder_app.command(name="list")
    def folder_list():
        """List all folders."""
        from ai_mini_box.infrastructure.database import get_db
        from .models import MessageCategory

        with get_db() as session:
            cats = session.execute(select(MessageCategory).order_by(MessageCategory.id)).scalars().all()
            if not cats:
                typer.echo("No folders defined.")
                return
            for c in cats:
                system_tag = typer.style(" [system]", dim=True) if c.is_system else ""
                typer.echo(f"  {c.id}: {c.name}{system_tag}  ({c.description})  {c.color}")

    @folder_app.command()
    def add(
        name: str = typer.Argument(..., help="Folder name"),
        description: str = typer.Option("", "--description", "-d", help="Folder description"),
        color: str = typer.Option("#6b7280", "--color", "-c", help="Hex color"),
    ):
        """Create a custom folder."""
        from ai_mini_box.infrastructure.database import get_db
        from .models import MessageCategory

        with get_db() as session:
            existing = session.execute(
                select(MessageCategory).where(MessageCategory.name == name)
            ).scalar_one_or_none()
            if existing:
                typer.echo(f"Error: Folder '{name}' already exists.")
                raise typer.Exit(1)
            cat = MessageCategory(name=name, description=description, color=color, is_system=False)
            session.add(cat)
            session.flush()
            session.refresh(cat)
            typer.echo(f"Folder created: {cat.id} - {cat.name}")

    @folder_app.command()
    def remove(name: str = typer.Argument(..., help="Folder name")):
        """Remove a custom folder (system folders protected)."""
        from ai_mini_box.infrastructure.database import get_db
        from .models import MessageCategory, MessageCategoryAssignment

        with get_db() as session:
            cat = session.execute(
                select(MessageCategory).where(MessageCategory.name == name)
            ).scalar_one_or_none()
            if cat is None:
                typer.echo(f"Error: Folder '{name}' not found.")
                raise typer.Exit(1)
            if cat.is_system:
                typer.echo("Error: Cannot remove system folder.")
                raise typer.Exit(1)
            session.execute(
                MessageCategoryAssignment.__table__.delete().where(
                    MessageCategoryAssignment.category_id == cat.id
                )
            )
            session.delete(cat)
            typer.echo(f"Folder removed: {name}")

    @folder_app.command()
    def classify(
        msg_id: int = typer.Argument(..., help="Message ID"),
    ):
        """Run folder classification for a single message."""
        from ai_mini_box.infrastructure.database import get_db
        from .models import MessageCategory, MessageCategoryAssignment

        try:
            pipeline = _get_pipeline()
        except Exception:
            typer.echo("Error: LLM pipeline not available.")
            raise typer.Exit(1)

        with get_db() as session:
            repos = RepoContainer(session)
            msg = repos.messages.get_by_id(msg_id)
            if msg is None:
                typer.echo(f"Error: Message #{msg_id} not found.")
                raise typer.Exit(1)

            cats = session.execute(select(MessageCategory)).scalars().all()
            if not cats:
                typer.echo("Error: No categories defined.")
                raise typer.Exit(1)

            result = pipeline.process(msg.text)
            typer.echo(f"Best category: {result.category}")

            folder_names = [c.name for c in cats]
            folder_result = pipeline._classifier.predict_folder(msg.text, folder_names)
            best_cat = None
            for c in cats:
                if c.name == folder_result:
                    best_cat = c
                    break
            if best_cat is None:
                for c in cats:
                    if c.name == result.category:
                        best_cat = c
                        break
            if best_cat is None:
                best_cat = cats[0]

            existing = session.execute(
                select(MessageCategoryAssignment).where(
                    MessageCategoryAssignment.message_id == msg_id,
                    MessageCategoryAssignment.category_id == best_cat.id,
                )
            ).scalar_one_or_none()
            if not existing:
                session.add(MessageCategoryAssignment(
                    message_id=msg_id,
                    category_id=best_cat.id,
                    assigned_by="manual",
                ))
                typer.echo(f"Assigned message #{msg_id} to '{best_cat.name}'.")
            else:
                typer.echo(f"Message #{msg_id} already assigned to '{best_cat.name}'.")


def _get_db_safe():
    from ai_mini_box.infrastructure.database import get_db
    return get_db()


class LlmConfigProvider:
    def get_config(self) -> dict:
        from .config import LlmConfig
        cfg = LlmConfig.load()
        return {
            "provider": cfg.provider,
            "model_path": cfg.model_path or "",
            "embeddings_model": getattr(cfg, "embeddings_model", "all-MiniLM-L6-v2"),
            "rag_enabled": cfg.rag_enabled,
            "rag_top_k": cfg.rag_top_k,
            "confidence_min": getattr(cfg, "confidence_min", 0.6),
            "batch_size": getattr(cfg, "batch_size", 50),
        }

    def set_config(self, config: dict) -> dict:
        from .config import LlmConfig
        cfg = LlmConfig.load()
        for key in ("provider", "model_path", "embeddings_model", "rag_top_k", "confidence_min", "batch_size"):
            if key in config:
                setattr(cfg, key, config[key])
        if "rag_enabled" in config:
            cfg.rag_enabled = bool(config["rag_enabled"])
        cfg.save()
        return {"success": True}

    def get_schema(self) -> dict:
        return {
            "$schema": "https://json-schemas.org/draft/2020-12/schema",
            "type": "object",
            "title": "LLM Plugin Config",
            "properties": {
                "provider": {"type": "string", "title": "Провайдер", "enum": ["local", "remote"], "default": "local"},
                "model_path": {"type": "string", "title": "Путь к модели", "default": ""},
                "embeddings_model": {"type": "string", "title": "Embeddings модель", "default": "all-MiniLM-L6-v2"},
                "rag_enabled": {"type": "boolean", "title": "RAG включён", "default": False},
                "rag_top_k": {"type": "integer", "title": "RAG top-K", "default": 3, "minimum": 1, "maximum": 20},
                "confidence_min": {"type": "number", "title": "Мин. confidence для шаблона", "default": 0.6, "minimum": 0.0, "maximum": 1.0},
                "batch_size": {"type": "integer", "title": "Размер батча для обучения", "default": 50, "minimum": 10},
            },
            "required": [],
        }


config_provider = LlmConfigProvider()
