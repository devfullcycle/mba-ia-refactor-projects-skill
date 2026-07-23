from flask import Blueprint, jsonify
from controllers import system_controller

system_bp = Blueprint("system", __name__)


@system_bp.route("/", methods=["GET"])
def index():
    body, status = system_controller.index()
    return jsonify(body), status


@system_bp.route("/health", methods=["GET"])
def health_check():
    body, status = system_controller.health_check()
    return jsonify(body), status


@system_bp.route("/admin/reset-db", methods=["POST"])
def reset_database():
    body, status = system_controller.reset_database()
    return jsonify(body), status


@system_bp.route("/admin/query", methods=["POST"])
def executar_query():
    body, status = system_controller.executar_query()
    return jsonify(body), status
