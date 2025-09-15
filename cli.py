def register_cli(app):
    @app.cli.command("seed")
    def seed_command():
        """Seed database with sample users, categories, and activities."""
        from .seed import main as _seed_main
        _seed_main()

