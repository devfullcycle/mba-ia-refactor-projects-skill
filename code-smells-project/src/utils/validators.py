"""Checagens de tipo compartilhadas pelos controllers (bool não conta como número)."""


def is_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def is_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def campo_texto(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""
