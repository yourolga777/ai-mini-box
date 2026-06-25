from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from ai_mini_box.core.services.registry import register_service, get_service

from .config import LlmConfig
from .service import LlmServiceImpl

logger.add("logs/plugin_llm.log", rotation="1 MB", retention=3)


def register(app: typer.Typer) -> None:
    """Entry point: register LLM service and CLI commands."""
    try:
        config = LlmConfig.load()
        service = LlmServiceImpl(config)
        register_service("llm", service)
        logger.info("LLM service registered (provider={})", config.provider)
    except Exception as e:
        logger.warning("LLM plugin skipped: {}", e)

    llm_app = typer.Typer(help="LLM commands")
    app.add_typer(llm_app, name="llm")

    @llm_app.command()
    def status():
        """Show LLM service status."""
        svc = get_service("llm")
        if svc is None:
            typer.echo("LLM: not active (plugin not registered)")
            return
        cfg = LlmConfig.load()
        typer.echo(f"Provider:   {cfg.provider}")
        typer.echo(f"Model:      {cfg.model_path if cfg.provider == 'local' else cfg.model_name or 'default'}")
        typer.echo(f"RAG:        {'enabled' if cfg.rag_enabled else 'disabled'}")
        typer.echo("Status:     active")

    @llm_app.command()
    def classify(
        text: str = typer.Argument(..., help="Message text to classify"),
    ):
        """Classify a message topic."""
        svc = get_service("llm")
        if svc is None:
            typer.echo("Error: LLM plugin is not active.")
            raise typer.Exit(1)
        result = svc.classify(text)
        if result:
            typer.echo(f"Topic: {result.value}")
        else:
            typer.echo("Topic: uncertain")

    @llm_app.command()
    def draft(
        text: str = typer.Argument(..., help="Message text"),
        topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Topic (optional)"),
    ):
        """Generate a draft response."""
        svc = get_service("llm")
        if svc is None:
            typer.echo("Error: LLM plugin is not active.")
            raise typer.Exit(1)
        from ai_mini_box.core.models import Topic as TopicEnum
        topic_enum = None
        if topic:
            try:
                topic_enum = TopicEnum(topic)
            except ValueError:
                typer.echo(f"Invalid topic: {topic}. Valid: {', '.join(t.value for t in TopicEnum)}")
                raise typer.Exit(1)
        result = svc.draft_response(text, topic=topic_enum)
        if result:
            typer.echo(result)
        else:
            typer.echo("Could not generate a draft.")

    @llm_app.command()
    def extract(
        text: str = typer.Argument(..., help="Message text"),
    ):
        """Extract entities from text."""
        svc = get_service("llm")
        if svc is None:
            typer.echo("Error: LLM plugin is not active.")
            raise typer.Exit(1)
        result = svc.extract_entities(text)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

    @llm_app.command()
    def download_model(
        model: str = typer.Argument(
            "Qwen/Qwen2.5-0.5B-Instruct-GGUF:q4_0",
            help="Hugging Face model ID (e.g. 'author/model:quant')",
        ),
        output_dir: str = typer.Option("data/models/", "--output-dir", "-o", help="Output directory"),
    ):
        """Download a GGUF model from Hugging Face Hub."""
        _do_download(model, output_dir)

    @llm_app.command()
    def ingest_kb(
        index_path: str = typer.Option("data/llm_rag_index.json", "--index", help="Index file path"),
    ):
        """Rebuild the RAG index from the Knowledge Base."""
        _do_ingest_kb(index_path)


def _do_download(model: str, output_dir: str) -> None:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        typer.echo(
            "Error: huggingface-hub is not installed.\n"
            "Run: pip install ai-mini-box-llm[download]"
        )
        raise typer.Exit(1)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Downloading {model}...")

    repo_id = model
    filename = None
    if ":" in model:
        parts = model.split(":", 1)
        repo_id = parts[0]
        filename = parts[1]

    try:
        if filename:
            local_path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=out)
        else:
            local_path = hf_hub_download(repo_id=repo_id, local_dir=out)
        typer.echo(f"Downloaded to: {local_path}")

        llm_cfg = LlmConfig.load()
        llm_cfg.model_path = str(local_path)
        llm_cfg.save()
        typer.echo(f"Updated llm_config.json: model_path = {local_path}")
    except Exception as e:
        typer.echo(f"Error downloading model: {e}")
        raise typer.Exit(1)


def _do_ingest_kb(index_path: str) -> None:
    svc = get_service("llm")
    if svc is None:
        typer.echo("Error: LLM plugin is not active.")
        raise typer.Exit(1)

    from .rag.retriever import rebuild_index

    typer.echo("Rebuilding RAG index from Knowledge Base...")
    count = rebuild_index(svc.provider, index_path=index_path)
    typer.echo(f"Index rebuilt: {count} entries saved to {index_path}")
