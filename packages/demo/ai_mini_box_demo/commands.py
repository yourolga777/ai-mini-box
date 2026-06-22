from typing import Optional

import typer
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Contact, MessageSource
from ai_mini_box.infrastructure.database import get_db


def register(app: typer.Typer):
    @app.command(name="demo-list")
    def list_contacts(
        limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
        offset: int = typer.Option(0, "--offset", "-o", help="Skip N items"),
    ):
        """List contacts."""
        with get_db() as session:
            repo = RepoContainer(session).contacts
            contacts = repo.list(limit=limit, offset=offset, sort="name")
            for c in contacts:
                typer.echo(f"{c.id}: {c.name} ({c.phone or '—'})")

    @app.command(name="demo-get")
    def get_contact(contact_id: int = typer.Argument(..., help="Contact ID")):
        """Get a contact by ID."""
        with get_db() as session:
            repo = RepoContainer(session).contacts
            c = repo.get_by_id(contact_id)
            if c is None:
                typer.echo(f"Contact #{contact_id} not found")
                raise typer.Exit(code=1)
            typer.echo(f"ID: {c.id}")
            typer.echo(f"Name: {c.name}")
            typer.echo(f"Phone: {c.phone or '—'}")
            typer.echo(f"Email: {c.email or '—'}")
            typer.echo(f"Telegram: {c.telegram or '—'}")
            typer.echo(f"Source: {c.source.value}")

    @app.command(name="demo-add")
    def add_contact(
        name: str = typer.Argument(..., help="Contact name"),
        phone: Optional[str] = typer.Option(None, "--phone", "-p", help="Phone number"),
        email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
        telegram: Optional[str] = typer.Option(None, "--telegram", "-t", help="Telegram handle"),
    ):
        """Add a new contact."""
        with get_db() as session:
            repo = RepoContainer(session).contacts
            contact = Contact(name=name, phone=phone, email=email, telegram=telegram)
            added = repo.add(contact)
            typer.echo(f"Created contact #{added.id}: {added.name}")
