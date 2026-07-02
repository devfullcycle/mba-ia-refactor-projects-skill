from flask import Blueprint
from controllers import sistema

bp = Blueprint("sistema", __name__)

@bp.route("/", methods=["GET"])
def index():
    return sistema.index()

@bp.route("/health", methods=["GET"])
def health_check():
    return sistema.health_check()
