from flask import request
from services import produto_service


def listar_produtos():
    produtos = produto_service.list_products()
    return {"dados": produtos, "sucesso": True}, 200


def buscar_produto(produto_id):
    return {"dados": produto_service.get_product(produto_id), "sucesso": True}, 200


def criar_produto():
    data = request.get_json() or {}
    novo_id = produto_service.create_product(data)
    return (
        {"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"},
        201,
    )


def atualizar_produto(produto_id):
    data = request.get_json() or {}
    produto_service.update_product(produto_id, data)
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar_produto(produto_id):
    produto_service.delete_product(produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)
    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)
    resultados = produto_service.search_products(termo, categoria, preco_min, preco_max)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
