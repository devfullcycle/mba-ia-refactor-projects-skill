"""Validação de entrada de Produto (compartilhada entre criação e atualização)."""
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN
from src.utils.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validar_produto(dados):
    """Valida o payload e devolve os campos normalizados. Mensagens preservam o contrato original."""
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"),
                            ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "") or ""
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str) or len(nome) < NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def parse_filtro_preco(nome_parametro, valor):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"Parâmetro {nome_parametro} inválido")
