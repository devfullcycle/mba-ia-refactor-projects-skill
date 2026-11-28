"""Index and health endpoints."""
from datetime import datetime

from flask import Blueprint


def build_system_routes():
    bp = Blueprint("system", __name__)

    @bp.get("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.now())}

    @bp.get("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return bp
