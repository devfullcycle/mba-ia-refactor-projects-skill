"""Entrypoint de compatibilidade: mantém `python app.py` e expõe `app` para servidores WSGI."""
from src.app import create_app, main

app = create_app()

if __name__ == "__main__":
    main(app)
