"""Validação de entrada na borda: presença, tipo e faixa; erro => AppError 400."""
import re

from services.constantes import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from services.excecoes import AppError

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return None


def _inteiro_positivo(valor):
    numero = _inteiro(valor)
    return numero if numero is not None and numero > 0 else None


def validar_produto(dados):
    if not isinstance(dados, dict) or not dados:
        raise AppError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise AppError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    preco = dados["preco"]
    estoque = _inteiro(dados["estoque"])

    if not isinstance(nome, str):
        raise AppError("Nome inválido")
    if not isinstance(descricao, str):
        raise AppError("Descrição inválida")
    if not _eh_numero(preco):
        raise AppError("Preço inválido")
    if estoque is None:
        raise AppError("Estoque inválido")
    if preco < 0:
        raise AppError("Preço não pode ser negativo")
    if estoque < 0:
        raise AppError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise AppError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise AppError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise AppError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    filtros = {"termo": args.get("q", ""), "categoria": args.get("categoria") or None}
    for campo in ("preco_min", "preco_max"):
        valor = args.get(campo)
        if valor:
            try:
                filtros[campo] = float(valor)
            except ValueError:
                raise AppError(f"{campo} inválido") from None
        else:
            filtros[campo] = None
    return filtros


def validar_usuario(dados):
    if not isinstance(dados, dict) or not dados:
        raise AppError("Dados inválidos")
    nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
    if not nome or not email or not senha:
        raise AppError("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise AppError("Nome, email e senha devem ser texto")
    if not _EMAIL.match(email):
        raise AppError("Email inválido")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise AppError("Email e senha são obrigatórios")
    return {"email": email, "senha": senha}


def validar_pedido(dados):
    if not isinstance(dados, dict) or not dados:
        raise AppError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise AppError("Usuario ID é obrigatório")
    if _inteiro_positivo(usuario_id) is None:
        raise AppError("Usuario ID inválido")
    if not itens:
        raise AppError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise AppError("Itens inválidos")

    itens_validos = []
    for item in itens:
        produto_id = _inteiro_positivo(item.get("produto_id")) if isinstance(item, dict) else None
        quantidade = _inteiro_positivo(item.get("quantidade")) if isinstance(item, dict) else None
        if produto_id is None or quantidade is None:
            raise AppError("Item inválido: produto_id e quantidade devem ser inteiros positivos")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})
    return {"usuario_id": _inteiro_positivo(usuario_id), "itens": itens_validos}


def validar_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    status = dados.get("status", "")
    if status not in STATUS_PEDIDO_VALIDOS:
        raise AppError("Status inválido")
    return status
