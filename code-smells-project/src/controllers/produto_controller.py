import logging

from src.models import produto_model
from src.utils.errors import NotFoundError, ValidationError
from src.utils.validators import is_inteiro, is_numero

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN = 2
NOME_MAX = 200


def _validar_dados_produto(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str) or not isinstance(descricao, str) or not isinstance(categoria, str):
        raise ValidationError("Nome, descrição e categoria devem ser texto")
    if not is_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not is_inteiro(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return nome, descricao, preco, estoque, categoria


def _parse_preco(valor, nome_parametro):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{nome_parametro} deve ser numérico")


def listar_produtos():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return produtos


def obter_produto(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def criar_produto(dados):
    produto_id = produto_model.criar(*_validar_dados_produto(dados))
    logger.info("Produto criado com ID: %s", produto_id)
    return produto_id


def atualizar_produto(produto_id, dados):
    obter_produto(produto_id)
    produto_model.atualizar(produto_id, *_validar_dados_produto(dados))


def deletar_produto(produto_id):
    """Exclusão lógica: o produto sai do catálogo, mas o histórico de pedidos continua íntegro."""
    obter_produto(produto_id)
    produto_model.desativar(produto_id)
    logger.info("Produto %s desativado", produto_id)


def buscar_produtos(termo, categoria, preco_min, preco_max):
    return produto_model.buscar(
        termo=termo,
        categoria=categoria,
        preco_min=_parse_preco(preco_min, "preco_min"),
        preco_max=_parse_preco(preco_max, "preco_max"),
    )
