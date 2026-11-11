from flask import current_app

from src.utils.dates import utc_now


def index():
    return {"message": current_app.config["APP_NAME"], "version": current_app.config["APP_VERSION"]}


def health():
    return {"status": "ok", "timestamp": str(utc_now())}
