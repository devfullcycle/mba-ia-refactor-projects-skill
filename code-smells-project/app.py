"""Application entrypoint."""

from __future__ import annotations

from src.app import create_app
from src.config.settings import load_settings
from src.db.database import init_db

settings = load_settings()
init_db(settings)
app = create_app(settings)

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://{settings.host}:{settings.port}")
    print("=" * 50)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
