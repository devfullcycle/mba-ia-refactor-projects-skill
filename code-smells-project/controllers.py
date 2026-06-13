from flask import current_app, jsonify, request

from errors import BadRequestError, UnauthorizedError
from security import admin_token_is_valid
import models
import services


def _admin_required():
    expected_token = current_app.config.get("ADMIN_API_TOKEN", "")
    provided_token = request.headers.get("X-Admin-Token")
    if not admin_token_is_valid(provided_token, expected_token):
        raise UnauthorizedError("Admin token required")


def listar_produtos():
    return jsonify({"dados": services.list_products(), "sucesso": True}), 200


def buscar_produto(id):
    return jsonify({"dados": services.get_product(id), "sucesso": True}), 200


def criar_produto():
    return jsonify({"dados": services.create_product(request.get_json(silent=True)), "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    return jsonify({"dados": services.update_product(id, request.get_json(silent=True)), "sucesso": True}), 200


def deletar_produto(id):
    return jsonify({"dados": services.delete_product(id), "sucesso": True}), 200


def buscar_produtos():
    resultados = services.search_products(dict(request.args))
    return jsonify({
        "dados": resultados,
        "total": len(resultados),
        "sucesso": True,
    }), 200


def listar_usuarios():
    return jsonify({"dados": services.list_users(), "sucesso": True}), 200


def buscar_usuario(id):
    return jsonify({"dados": services.get_user(id), "sucesso": True}), 200


def criar_usuario():
    return jsonify({"dados": services.create_user(request.get_json(silent=True)), "sucesso": True}), 201


def login():
    return jsonify({"dados": services.login_user(request.get_json(silent=True)), "sucesso": True, "mensagem": "Login OK"}), 200


def criar_pedido():
    resultado = services.create_order(request.get_json(silent=True))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": services.list_user_orders(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": services.list_orders(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    return jsonify({"dados": services.update_order_status(pedido_id, request.get_json(silent=True)), "sucesso": True}), 200


def relatorio_vendas():
    return jsonify({"dados": services.sales_report(), "sucesso": True}), 200


def health_check():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": models.count_produtos(),
            "usuarios": models.count_usuarios(),
            "pedidos": models.count_pedidos(),
        },
        "versao": "1.0.0",
        "ambiente": "desenvolvimento" if current_app.debug else "producao",
    }), 200


def reset_database():
    _admin_required()
    models.reset_database()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    _admin_required()
    dados = request.get_json(silent=True) or {}
    if not isinstance(dados, dict):
        raise BadRequestError("Dados invalidos")

    query = dados.get("sql", "")
    if not query:
        raise BadRequestError("Query nao informada")

    try:
        resultado = models.executar_query_leitura(query)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from None
    return jsonify({"dados": resultado, "sucesso": True}), 200
