"""Validação de Produto — regra única usada por criação e atualização.

No legado, criar e atualizar tinham validações divergentes: o `PUT` aceitava nome fora do
tamanho permitido e categoria inexistente, que o `POST` rejeitava.
"""
from src.config.settings import CATEGORIAS_VALIDAS
from src.middlewares.error_handler import ValidationError

NOME_MIN = 2
NOME_MAX = 200
CATEGORIA_PADRAO = "geral"


def _numero(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{campo} deve ser numérico")
    return valor


def validate_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = str(dados["nome"]).strip()
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")

    preco = _numero(dados["preco"], "Preço")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")

    estoque = _numero(dados["estoque"], "Estoque")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    categoria = dados.get("categoria") or CATEGORIA_PADRAO
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            "Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS))
        )

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": int(estoque),
        "categoria": categoria,
    }


def validate_filtros_busca(args):
    """Normaliza os filtros de `/produtos/busca`, convertendo preços com segurança."""

    def _preco(nome_campo):
        bruto = args.get(nome_campo)
        if bruto in (None, ""):
            return None
        try:
            return float(bruto)
        except (TypeError, ValueError):
            raise ValidationError(f"{nome_campo} deve ser numérico")

    return {
        "termo": args.get("q", "") or None,
        "categoria": args.get("categoria") or None,
        "preco_min": _preco("preco_min"),
        "preco_max": _preco("preco_max"),
    }
