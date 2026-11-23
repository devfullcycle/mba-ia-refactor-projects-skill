"""Entry point: `python app.py`. Host, port and debug come from the environment (see .env.example)."""
from src.app import create_app
from src.models.database import db

app = create_app()

__all__ = ["app", "db"]

if __name__ == "__main__":
    settings = app.extensions["settings"]
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
