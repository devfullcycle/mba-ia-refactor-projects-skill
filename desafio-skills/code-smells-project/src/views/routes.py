from flask import Blueprint, jsonify, request, current_app

from src.database import get_db
from src.repositories import orders, products, users

api_bp = Blueprint("api", __name__)


@api_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    try:
        produtos = products.get_todos_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", type=float)
        preco_max = request.args.get("preco_max", type=float)
        resultados = products.buscar_produtos(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/produtos/<int:pid>", methods=["GET"])
def buscar_produto(pid):
    try:
        produto = products.get_produto_por_id(pid)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/produtos", methods=["POST"])
def criar_produto():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                return jsonify({"erro": f"{campo} é obrigatório"}), 400
        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")
        if preco < 0 or estoque < 0:
            return jsonify({"erro": "Preço e estoque devem ser não negativos"}), 400
        if len(nome) < 2 or len(nome) > 200:
            return jsonify({"erro": "Nome inválido"}), 400
        categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
        if categoria not in categorias_validas:
            return jsonify({"erro": "Categoria inválida", "validas": categorias_validas}), 400
        new_id = products.criar_produto(nome, descricao, preco, estoque, categoria)
        return jsonify({"dados": {"id": new_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/produtos/<int:pid>", methods=["PUT"])
def atualizar_produto(pid):
    try:
        dados = request.get_json()
        if not products.get_produto_por_id(pid):
            return jsonify({"erro": "Produto não encontrado"}), 404
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                return jsonify({"erro": f"{campo} é obrigatório"}), 400
        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")
        if preco < 0 or estoque < 0:
            return jsonify({"erro": "Preço e estoque devem ser não negativos"}), 400
        products.atualizar_produto(pid, nome, descricao, preco, estoque, categoria)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/produtos/<int:pid>", methods=["DELETE"])
def deletar_produto(pid):
    try:
        if not products.get_produto_por_id(pid):
            return jsonify({"erro": "Produto não encontrado"}), 404
        products.deletar_produto(pid)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        return jsonify({"dados": users.get_todos_usuarios(), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/usuarios/<int:uid>", methods=["GET"])
def buscar_usuario(uid):
    try:
        u = users.get_usuario_por_id(uid)
        if u:
            return jsonify({"dados": u, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400
        new_id = users.criar_usuario(nome, email, senha)
        return jsonify({"dados": {"id": new_id}, "sucesso": True}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/login", methods=["POST"])
def login():
    try:
        dados = request.get_json() or {}
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400
        usuario = users.login_usuario(email, senha)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
        resultado = orders.criar_pedido(usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = orders.get_pedidos_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    try:
        pedidos = orders.get_todos_pedidos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json() or {}
        novo_status = dados.get("status", "")
        valid = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
        if novo_status not in valid:
            return jsonify({"erro": "Status inválido"}), 400
        orders.atualizar_status_pedido(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    try:
        rel = orders.relatorio_vendas()
        return jsonify({"dados": rel, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route("/health", methods=["GET"])
def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos_count = cursor.fetchone()[0]
        return jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos_count},
                "versao": "1.0.0",
            }
        ), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500


def register_routes(app):
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": "1.0.0",
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        )

    @app.route("/admin/reset-db", methods=["POST"])
    def reset_database():
        if not current_app.config.get("ENABLE_ADMIN_RESET"):
            return jsonify({"erro": "Reset desabilitado (defina ENABLE_ADMIN_RESET=true)"}), 403
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
