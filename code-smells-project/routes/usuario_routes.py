"""Endpoints HTTP do domínio de usuários e autenticação."""

from flask import Blueprint
from controllers import usuario_controller

usuarios_bp = Blueprint("usuarios", __name__)

usuarios_bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
usuarios_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
usuarios_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])