from flask import Blueprint
from controllers.usuario_controller import UsuarioController

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.route("/usuarios", methods=["GET"])(UsuarioController.listar_usuarios)
usuario_bp.route("/usuarios/<int:id>", methods=["GET"])(UsuarioController.buscar_usuario)
usuario_bp.route("/usuarios", methods=["POST"])(UsuarioController.criar_usuario)
usuario_bp.route("/login", methods=["POST"])(UsuarioController.login)
