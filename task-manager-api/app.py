"""Entry point — `python app.py` (also exposes `app` for WSGI servers)."""
from src.app import create_app
from src.models.database import db  # noqa: F401  (kept for scripts doing `from app import app, db`)

app = create_app()

if __name__ == "__main__":
    settings = app.extensions["settings"]
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
