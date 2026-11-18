from config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
from exceptions import ValidationError


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados):
    """Valida o payload de criação/atualização e devolve os campos normalizados."""
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

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _eh_numero(preco):
        raise ValidationError("Preço inválido")
    if not _eh_numero(estoque):
        raise ValidationError("Estoque inválido")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_filtros_busca(args):
    """Converte os query params de /produtos/busca."""
    filtros = {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria", None),
        "preco_min": None,
        "preco_max": None,
    }
    for campo in ("preco_min", "preco_max"):
        bruto = args.get(campo, None)
        if bruto:
            try:
                filtros[campo] = float(bruto)
            except ValueError:
                raise ValidationError(campo + " inválido")
    return filtros
