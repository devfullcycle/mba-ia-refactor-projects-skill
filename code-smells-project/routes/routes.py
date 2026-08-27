from flask import jsonify, request
from database import get_db
import controllers.produto_controller as produto_controller
import controllers.usuario_controller as usuario_controller
import controllers.pedido_controller as pedido_controller
import controllers.relatorio_controller as relatorio_controller
import controllers.health_controller as health_controller

def setup_routes(app):
    app.add_url_rule("/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", produto_controller.criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar_produto, methods=["DELETE"])

    app.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

    app.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_controller.listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_controller.atualizar_status_pedido, methods=["PUT"])

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.relatorio_vendas, methods=["GET"])

    app.add_url_rule("/health", "health_check", health_controller.health_check, methods=["GET"])

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        })

    @app.route("/admin/reset-db", methods=["POST"])
    @admin_required
    def reset_database():
        # Cleaned up and made safe/controlled
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        print("!!! BANCO DE DADOS RESETADO !!!")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

def admin_required(f):
    from functools import wraps
    from flask import request, jsonify
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica token ou credencial admin na requisição
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != "Bearer segredo-admin-da-app":
            return jsonify({"erro": "Acesso não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated_function
