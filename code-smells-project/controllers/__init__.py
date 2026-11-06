from flask import current_app


def servicos():
    """Serviços montados no composition root (app.create_app)."""
    return current_app.extensions["servicos"]
