"""Rotas de sistema (índice e health check)."""
from flask import Blueprint

from utils.clock import utcnow


def create_system_routes(settings):
    bp = Blueprint("system", __name__)

    @bp.get("/health")
    def health():
        return {"status": "ok", "timestamp": str(utcnow())}

    @bp.get("/")
    def index():
        return {"message": settings.APP_NAME, "version": settings.APP_VERSION}

    return bp
