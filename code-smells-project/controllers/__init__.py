"""Controllers — orquestração pura: request → validação → service → resposta.

Cada handler tem poucas linhas, não acessa banco e não contém regra de
negócio (resolve ARCH-01/ARCH-02). Erros de domínio sobem para o handler
central de erros.
"""

from flask import g, jsonify, request

from errors import NaoAutorizadoError, ProibidoError
from schemas import validators
from services import auth_service, pedido_service, produto_service, usuario_service


# ---------------------------------------------------------------- produtos ---
def listar_produtos():
    produtos = produto_service.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    return jsonify({"dados": produto_service.buscar_por_id(id), "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = _float_opcional(request.args.get("preco_min"))
    preco_max = _float_opcional(request.args.get("preco_max"))

    resultados, total = produto_service.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": total, "sucesso": True}), 200


def criar_produto():
    dados = validators.produto(request.get_json(silent=True))
    resultado = produto_service.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = validators.produto(request.get_json(silent=True))
    produto_service.atualizar(id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto_service.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


# ---------------------------------------------------------------- usuarios ---
def listar_usuarios():
    return jsonify({"dados": usuario_service.listar(), "sucesso": True}), 200


def buscar_usuario(id):
    return jsonify({"dados": usuario_service.buscar_por_id(id), "sucesso": True}), 200


def criar_usuario():
    dados = validators.usuario(request.get_json(silent=True))
    resultado = usuario_service.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True}), 201


def login():
    dados = validators.login(request.get_json(silent=True))
    usuario = usuario_service.autenticar(dados["email"], dados["senha"])
    token = auth_service.emitir_token(usuario)
    return jsonify({
        "dados": usuario,
        "token": token,
        "sucesso": True,
        "mensagem": "Login OK",
    }), 200


# ----------------------------------------------------------------- pedidos ---
def criar_pedido():
    dados = validators.pedido(request.get_json(silent=True))

    usuario = getattr(g, "usuario_atual", None)
    if usuario is None:
        raise NaoAutorizadoError("Token de acesso ausente")
    if dados["usuario_id"] != usuario["id"]:
        raise ProibidoError("Cliente só pode criar pedido para si mesmo")

    resultado = pedido_service.criar(dados["usuario_id"], dados["itens"])
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_service.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_service.listar(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    novo_status = validators.status_pedido(
        request.get_json(silent=True), status_validos=_status_validos()
    )
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


# --------------------------------------------------------------- relatorios ---
def relatorio_vendas():
    return jsonify({"dados": pedido_service.relatorio_vendas(), "sucesso": True}), 200


# ---------------------------------------------------------------- operacao ---
def health_check():
    from services import health_service

    return jsonify(health_service.status()), 200


# ---------------------------------------------------------------- helpers ---
def _float_opcional(valor):
    if valor in (None, ""):
        return None
    return float(valor)


def _status_validos():
    from config import Config

    return Config.STATUS_PEDIDO_VALIDOS
