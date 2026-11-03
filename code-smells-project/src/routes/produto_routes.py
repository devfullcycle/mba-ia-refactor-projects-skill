from flask import Blueprint, jsonify, request

from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)


@produto_bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produto_controller.listar_produtos(), "sucesso": True}), 200


@produto_bp.get("/produtos/busca")
def buscar_produtos():
    resultados = produto_controller.buscar_produtos(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=request.args.get("preco_min"),
        preco_max=request.args.get("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.obter_produto(produto_id), "sucesso": True}), 200


@produto_bp.post("/produtos")
def criar_produto():
    produto_id = produto_controller.criar_produto(request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id):
    produto_controller.atualizar_produto(produto_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id):
    produto_controller.deletar_produto(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
