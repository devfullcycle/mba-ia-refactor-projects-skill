from flask import Blueprint, jsonify, request


def create_produto_routes(controller):
    bp = Blueprint("produtos", __name__)

    @bp.get("/produtos")
    def listar_produtos():
        return jsonify({"dados": controller.listar(), "sucesso": True}), 200

    @bp.get("/produtos/busca")
    def buscar_produtos():
        resultados = controller.pesquisar(request.args)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        return jsonify({"dados": controller.obter(produto_id), "sucesso": True}), 200

    @bp.post("/produtos")
    def criar_produto():
        produto_id = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        controller.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
