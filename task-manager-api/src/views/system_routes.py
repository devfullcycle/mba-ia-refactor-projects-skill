from datetime import datetime

from flask import Blueprint

API_NAME = "Task Manager API"
API_VERSION = "1.0"


def build_system_routes():
    bp = Blueprint("system", __name__)

    @bp.get("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.now())}

    @bp.get("/")
    def index():
        return {"message": API_NAME, "version": API_VERSION}

    return bp
