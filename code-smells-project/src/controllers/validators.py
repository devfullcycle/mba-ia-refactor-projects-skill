"""Validação centralizada de entrada (reutilizada por criação e atualização)."""
from typing import Optional

from .errors import ValidationError

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200


def require_object(dados) -> dict:
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def _is_number(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _is_int(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def require_fields(dados: dict, *campos_rotulos) -> None:
    for campo, rotulo in campos_rotulos:
        if campo not in dados or dados[campo] is None:
            raise ValidationError(f"{rotulo} é obrigatório")


def validar_produto(dados, categorias_validas, categoria_padrao: str) -> dict:
    dados = require_object(dados)
    require_fields(dados, ("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque"))

    nome = dados["nome"]
    descricao = dados.get("descricao") or ""
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria") or categoria_padrao

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _is_int(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in categorias_validas:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(categorias_validas)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def parse_optional_float(valor: Optional[str], campo: str) -> Optional[float]:
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} deve ser numérico") from None


def validar_usuario(dados) -> dict:
    dados = require_object(dados)
    nome, email, senha = dados.get("nome"), dados.get("email"), dados.get("senha")
    if not all(isinstance(v, str) and v for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados) -> dict:
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email"), dados.get("senha")
    if not all(isinstance(v, str) and v for v in (email, senha)):
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "senha": senha}


def validar_pedido(dados) -> dict:
    dados = require_object(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens")

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_int(usuario_id) or usuario_id <= 0:
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validos = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item inválido")
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if not _is_int(produto_id) or produto_id <= 0:
            raise ValidationError("Item inválido: produto_id deve ser um inteiro positivo")
        if not _is_int(quantidade) or quantidade <= 0:
            raise ValidationError("Item inválido: quantidade deve ser um inteiro maior que zero")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})

    return {"usuario_id": usuario_id, "itens": itens_validos}


def validar_status(dados, status_validos) -> str:
    dados = dados if isinstance(dados, dict) else {}
    status = dados.get("status")
    if status not in status_validos:
        raise ValidationError("Status inválido")
    return status
