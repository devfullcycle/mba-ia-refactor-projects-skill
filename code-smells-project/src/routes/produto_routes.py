from flask import Blueprint, request

from src.controllers import produto_controller
from src.middlewares.auth import admin_required
from src.utils.responses import sucesso

produto_bp = Blueprint("produtos", __name__)


@produto_bp.get("/produtos")
def listar_produtos():
    return sucesso(produto_controller.listar_produtos())


@produto_bp.get("/produtos/busca")
def buscar_produtos():
    resultados = produto_controller.buscar_produtos(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=request.args.get("preco_min"),
        preco_max=request.args.get("preco_max"),
    )
    return sucesso(resultados, total=len(resultados))


@produto_bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return sucesso(produto_controller.obter_produto(produto_id))


@produto_bp.post("/produtos")
@admin_required
def criar_produto():
    produto_id = produto_controller.criar_produto(request.get_json(silent=True))
    return sucesso({"id": produto_id}, status=201, mensagem="Produto criado")


@produto_bp.put("/produtos/<int:produto_id>")
@admin_required
def atualizar_produto(produto_id):
    produto_controller.atualizar_produto(produto_id, request.get_json(silent=True))
    return sucesso(mensagem="Produto atualizado")


@produto_bp.delete("/produtos/<int:produto_id>")
@admin_required
def deletar_produto(produto_id):
    produto_controller.deletar_produto(produto_id)
    return sucesso(mensagem="Produto deletado")
