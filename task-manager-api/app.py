"""Entry point — keeps `python app.py` working. All wiring lives in src/app.py:create_app()."""
import logging

from src.app import create_app
from src.config.settings import load_settings
from src.models.database import db  # noqa: F401  (re-exported for scripts: `from app import app, db`)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = load_settings()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
