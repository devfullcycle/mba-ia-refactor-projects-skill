"""DTOs de saída: lista branca de campos (senha/hash e configuração interna nunca saem)."""

CAMPOS_PRODUTO = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
CAMPOS_USUARIO = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_USUARIO_LOGIN = ("id", "nome", "email", "tipo")
CAMPOS_PEDIDO = ("id", "usuario_id", "status", "total", "criado_em")
CAMPOS_ITEM_PEDIDO = ("produto_id", "produto_nome", "quantidade", "preco_unitario")


def _filtrar(registro, campos):
    return {campo: registro[campo] for campo in campos}


def produto_publico(produto):
    return _filtrar(produto, CAMPOS_PRODUTO)


def usuario_publico(usuario):
    return _filtrar(usuario, CAMPOS_USUARIO)


def usuario_login(usuario, token):
    return {**_filtrar(usuario, CAMPOS_USUARIO_LOGIN), "token": token}


def pedido_publico(pedido):
    return {
        **_filtrar(pedido, CAMPOS_PEDIDO),
        "itens": [_filtrar(item, CAMPOS_ITEM_PEDIDO) for item in pedido["itens"]],
    }
