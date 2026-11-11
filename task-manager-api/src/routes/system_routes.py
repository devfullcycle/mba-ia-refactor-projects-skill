from flask import Blueprint, jsonify

from src.controllers import system_controller

system_bp = Blueprint("system", __name__)


@system_bp.route("/", methods=["GET"])
def index():
    return jsonify(system_controller.index()), 200


@system_bp.route("/health", methods=["GET"])
def health():
    return jsonify(system_controller.health()), 200
