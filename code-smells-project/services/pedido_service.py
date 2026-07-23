from core.db import get_db
from core.errors import NotFoundError, ValidationError
from models import pedido_model
from services import notification_service


def _validate_items(itens):
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item precisa de produto_id e quantidade")
        if not isinstance(item["quantidade"], int) or item["quantidade"] <= 0:
            raise ValidationError("quantidade deve ser um inteiro positivo")


def create_order(usuario_id, itens):
    _validate_items(itens)
    db = get_db()
    pedido_id = None
    total = 0
    try:
        db.execute("BEGIN")
        for item in itens:
            produto = db.execute(
                "SELECT preco, estoque, nome FROM produtos WHERE id = ?",
                (item["produto_id"],),
            ).fetchone()
            if produto is None:
                raise NotFoundError(
                    "Produto " + str(item["produto_id"]) + " nao encontrado"
                )
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(
                    "Estoque insuficiente para " + produto["nome"]
                )
            total += produto["preco"] * item["quantidade"]

        cur = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, "pendente", total),
        )
        pedido_id = cur.lastrowid

        for item in itens:
            produto = db.execute(
                "SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise

    notification_service.notify_order_created(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def list_orders_by_user(usuario_id):
    return pedido_model.list_by_user(usuario_id)


def list_all_orders():
    return pedido_model.list_all()


def update_order_status(pedido_id, novo_status):
    pedido_model.update_status(pedido_id, novo_status)
    notification_service.notify_order_status(pedido_id, novo_status)
