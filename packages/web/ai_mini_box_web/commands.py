import typer


def register(app: typer.Typer):
    @app.command()
    def serve(
        host: str = typer.Option("127.0.0.1", help="Host to bind"),
        port: int = typer.Option(8080, help="Port to bind"),
        reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    ):
        """Start the web interface server."""
        import uvicorn

        uvicorn.run("ai_mini_box_web.server:app", host=host, port=port, reload=reload)
