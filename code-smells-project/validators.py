"""Validação de entrada na borda (mensagens e status originais preservados)."""
from config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from middlewares.error_handler import AppError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validar_produto(dados):
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos", 400)
    if "nome" not in dados:
        raise AppError("Nome é obrigatório", 400)
    if "preco" not in dados:
        raise AppError("Preço é obrigatório", 400)
    if "estoque" not in dados:
        raise AppError("Estoque é obrigatório", 400)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise AppError("Nome deve ser texto", 400)
    if not isinstance(descricao, str):
        raise AppError("Descrição deve ser texto", 400)
    if not _is_number(preco):
        raise AppError("Preço deve ser numérico", 400)
    if not _is_int(estoque):
        raise AppError("Estoque deve ser um número inteiro", 400)

    if preco < 0:
        raise AppError("Preço não pode ser negativo", 400)
    if estoque < 0:
        raise AppError("Estoque não pode ser negativo", 400)
    if len(nome) < NOME_PRODUTO_MIN:
        raise AppError("Nome muito curto", 400)
    if len(nome) > NOME_PRODUTO_MAX:
        raise AppError("Nome muito longo", 400)
    if categoria not in CATEGORIAS_VALIDAS:
        raise AppError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS), 400)

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    def _to_float(nome):
        valor = args.get(nome, None)
        if not valor:
            return None
        try:
            return float(valor)
        except ValueError:
            raise AppError("Parâmetro " + nome + " deve ser numérico", 400)

    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria", None),
        "preco_min": _to_float("preco_min"),
        "preco_max": _to_float("preco_max"),
    }


def validar_novo_usuario(dados):
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos", 400)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise AppError("Nome, email e senha são obrigatórios", 400)
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise AppError("Nome, email e senha devem ser texto", 400)
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise AppError("Email e senha são obrigatórios", 400)
    if not isinstance(email, str) or not isinstance(senha, str):
        raise AppError("Email e senha devem ser texto", 400)
    return {"email": email, "senha": senha}


def validar_novo_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise AppError("Dados inválidos", 400)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise AppError("Usuario ID é obrigatório", 400)
    if not itens or not isinstance(itens, list):
        raise AppError("Pedido deve ter pelo menos 1 item", 400)
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _is_int(item.get("produto_id"))
            or not _is_int(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise AppError("Item inválido: informe produto_id e quantidade (inteiro positivo)", 400)
    return {"usuario_id": usuario_id, "itens": itens}


def validar_status_pedido(dados):
    dados = dados if isinstance(dados, dict) else {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise AppError("Status inválido", 400)
    return novo_status
