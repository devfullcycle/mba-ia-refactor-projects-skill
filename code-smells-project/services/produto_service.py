"""Regras de negócio e validação do domínio de produtos."""

from models import produto_model
from config import settings


class ProdutoInvalidoError(Exception):
    """Levantada quando os dados do produto violam regras de validação."""


def validar_dados_produto(dados, obrigatorio_nome_preco_estoque=True):
    if not dados:
        raise ProdutoInvalidoError("Dados inválidos")

    nome = dados.get("nome", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")

    if obrigatorio_nome_preco_estoque:
        if "nome" not in dados:
            raise ProdutoInvalidoError("Nome é obrigatório")
        if "preco" not in dados:
            raise ProdutoInvalidoError("Preço é obrigatório")
        if "estoque" not in dados:
            raise ProdutoInvalidoError("Estoque é obrigatório")

    if preco is not None and preco < 0:
        raise ProdutoInvalidoError("Preço não pode ser negativo")
    if estoque is not None and estoque < 0:
        raise ProdutoInvalidoError("Estoque não pode ser negativo")
    if nome and len(nome) < 2:
        raise ProdutoInvalidoError("Nome muito curto")
    if nome and len(nome) > 200:
        raise ProdutoInvalidoError("Nome muito longo")

    categoria = dados.get("categoria", "geral")
    if categoria not in settings.CATEGORIAS_VALIDAS:
        raise ProdutoInvalidoError(f"Categoria inválida. Válidas: {settings.CATEGORIAS_VALIDAS}")


def criar(dados):
    validar_dados_produto(dados)
    return produto_model.criar_produto(dados)


def atualizar(produto_id, dados):
    if not produto_model.get_produto_por_id(produto_id):
        raise ProdutoInvalidoError("Produto não encontrado")
    validar_dados_produto(dados)
    return produto_model.atualizar_produto(produto_id, dados)


def deletar(produto_id):
    if not produto_model.get_produto_por_id(produto_id):
        raise ProdutoInvalidoError("Produto não encontrado")
    return produto_model.deletar_produto(produto_id)


def listar():
    return produto_model.get_todos_produtos()


def buscar(termo, categoria, preco_min, preco_max):
    return produto_model.buscar_produtos_por_filtro(termo, categoria, preco_min, preco_max)
def obter(produto_id):
    return produto_model.get_produto_por_id(produto_id)
