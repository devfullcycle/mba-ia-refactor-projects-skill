from flask import Blueprint, jsonify, request

from src.controllers import auth_controller

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    return jsonify(auth_controller.login(request.get_json(silent=True))), 200
