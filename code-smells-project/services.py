import secrets

from errors import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
import models
from security import hash_password, verify_password


VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
VALID_ORDER_STATUSES = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def _require_dict(payload):
    if not isinstance(payload, dict):
        raise BadRequestError("Dados invalidos")
    return payload


def _get_required_string(payload, field, max_length=None):
    value = payload.get(field, "")
    if not isinstance(value, str) or not value.strip():
        raise BadRequestError(f"{field.capitalize()} e obrigatorio")
    value = value.strip()
    if max_length is not None and len(value) > max_length:
        raise BadRequestError(f"{field.capitalize()} muito longo")
    return value


def _get_required_number(payload, field):
    value = payload.get(field, None)
    if value is None or isinstance(value, bool):
        raise BadRequestError(f"{field.capitalize()} e obrigatorio")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise BadRequestError(f"{field.capitalize()} invalido") from None


def _get_required_integer(payload, field):
    value = payload.get(field, None)
    if value is None or isinstance(value, bool):
        raise BadRequestError(f"{field.capitalize()} e obrigatorio")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise BadRequestError(f"{field.capitalize()} invalido") from None


def _normalize_optional_string(payload, field, default=""):
    value = payload.get(field, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise BadRequestError(f"{field.capitalize()} invalido")
    return value.strip()


def list_products():
    return models.get_todos_produtos()


def get_product(product_id):
    produto = models.get_produto_por_id(product_id)
    if not produto:
        raise NotFoundError("Produto nao encontrado")
    return produto


def create_product(payload):
    data = _require_dict(payload)
    nome = _get_required_string(data, "nome", max_length=200)
    descricao = _normalize_optional_string(data, "descricao", "")
    preco = _get_required_number(data, "preco")
    estoque = _get_required_integer(data, "estoque")
    categoria = _normalize_optional_string(data, "categoria", "geral")

    if preco < 0:
        raise BadRequestError("Preco nao pode ser negativo")
    if estoque < 0:
        raise BadRequestError("Estoque nao pode ser negativo")
    if len(nome) < 2:
        raise BadRequestError("Nome muito curto")
    if categoria not in VALID_CATEGORIES:
        raise BadRequestError(f"Categoria invalida. Validas: {VALID_CATEGORIES}")

    product_id = models.criar_produto(nome, descricao, preco, estoque, categoria)
    return {"id": product_id}


def update_product(product_id, payload):
    if not models.get_produto_por_id(product_id):
        raise NotFoundError("Produto nao encontrado")

    data = _require_dict(payload)
    nome = _get_required_string(data, "nome", max_length=200)
    descricao = _normalize_optional_string(data, "descricao", "")
    preco = _get_required_number(data, "preco")
    estoque = _get_required_integer(data, "estoque")
    categoria = _normalize_optional_string(data, "categoria", "geral")

    if preco < 0:
        raise BadRequestError("Preco nao pode ser negativo")
    if estoque < 0:
        raise BadRequestError("Estoque nao pode ser negativo")
    if categoria not in VALID_CATEGORIES:
        raise BadRequestError(f"Categoria invalida. Validas: {VALID_CATEGORIES}")

    updated = models.atualizar_produto(product_id, nome, descricao, preco, estoque, categoria)
    if not updated:
        raise NotFoundError("Produto nao encontrado")
    return {"mensagem": "Produto atualizado"}


def delete_product(product_id):
    if not models.get_produto_por_id(product_id):
        raise NotFoundError("Produto nao encontrado")
    deleted = models.deletar_produto(product_id)
    if not deleted:
        raise NotFoundError("Produto nao encontrado")
    return {"mensagem": "Produto deletado"}


def search_products(params):
    data = _require_dict(params)
    termo = data.get("q", "") or ""
    categoria = data.get("categoria", None)
    preco_min = data.get("preco_min", None)
    preco_max = data.get("preco_max", None)

    if categoria is not None and categoria != "" and not isinstance(categoria, str):
        raise BadRequestError("Categoria invalida")

    if preco_min not in (None, ""):
        try:
            preco_min = float(preco_min)
        except (TypeError, ValueError):
            raise BadRequestError("preco_min invalido") from None
    else:
        preco_min = None

    if preco_max not in (None, ""):
        try:
            preco_max = float(preco_max)
        except (TypeError, ValueError):
            raise BadRequestError("preco_max invalido") from None
    else:
        preco_max = None

    categoria = categoria or None
    return models.buscar_produtos(termo, categoria, preco_min, preco_max)


def list_users():
    return models.get_todos_usuarios()


def get_user(user_id):
    usuario = models.get_usuario_por_id(user_id)
    if not usuario:
        raise NotFoundError("Usuario nao encontrado")
    return usuario


def create_user(payload):
    data = _require_dict(payload)
    nome = _get_required_string(data, "nome", max_length=120)
    email = _get_required_string(data, "email", max_length=255)
    senha = _get_required_string(data, "senha", max_length=255)

    if models.get_usuario_por_email(email):
        raise ConflictError("Email ja cadastrado")

    user_id = models.criar_usuario(nome, email, hash_password(senha))
    return {"id": user_id}


def login_user(payload):
    data = _require_dict(payload)
    email = _get_required_string(data, "email", max_length=255)
    senha = _get_required_string(data, "senha", max_length=255)

    usuario = models.get_usuario_com_senha_por_email(email)
    if not usuario or not verify_password(senha, usuario["senha"]):
        raise UnauthorizedError("Email ou senha invalidos")

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    }


def create_order(payload):
    data = _require_dict(payload)
    usuario_id = _get_required_integer(data, "usuario_id")
    itens = data.get("itens", [])
    if not isinstance(itens, list) or len(itens) == 0:
        raise BadRequestError("Pedido deve ter pelo menos 1 item")

    if not models.get_usuario_por_id(usuario_id):
        raise NotFoundError("Usuario nao encontrado")

    normalized_items = []
    for item in itens:
        if not isinstance(item, dict):
            raise BadRequestError("Item invalido")
        produto_id = _get_required_integer(item, "produto_id")
        quantidade = _get_required_integer(item, "quantidade")
        if quantidade <= 0:
            raise BadRequestError("Quantidade deve ser maior que zero")
        normalized_items.append({"produto_id": produto_id, "quantidade": quantidade})

    try:
        return models.criar_pedido(usuario_id, normalized_items)
    except LookupError as exc:
        raise NotFoundError(str(exc)) from None
    except ValueError as exc:
        raise BadRequestError(str(exc)) from None


def list_user_orders(user_id):
    return models.get_pedidos_usuario(user_id)


def list_orders():
    return models.get_todos_pedidos()


def update_order_status(order_id, payload):
    data = _require_dict(payload)
    novo_status = _get_required_string(data, "status", max_length=30)
    if novo_status not in VALID_ORDER_STATUSES:
        raise BadRequestError("Status invalido")

    updated = models.atualizar_status_pedido(order_id, novo_status)
    if not updated:
        raise NotFoundError("Pedido nao encontrado")
    return {"mensagem": "Status atualizado"}


def sales_report():
    return models.relatorio_vendas()
