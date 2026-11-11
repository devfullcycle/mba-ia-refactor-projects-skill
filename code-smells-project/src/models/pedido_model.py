from enum import Enum

from src.config.database import get_db


class StatusPedido(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

    @classmethod
    def valores(cls):
        return [status.value for status in cls]


class EstoqueInsuficienteError(Exception):
    def __init__(self, produto_id):
        super().__init__(produto_id)
        self.produto_id = produto_id


class StatusDesatualizadoError(Exception):
    """O pedido mudou de status entre a leitura e a atualização (requisições concorrentes)."""


def criar(usuario_id, itens, total):
    """Cria pedido, itens e baixa de estoque em uma única transação.

    `itens` = [{"produto_id", "quantidade", "preco_unitario"}]. A baixa só ocorre se ainda
    houver estoque no momento do UPDATE; caso contrário a transação inteira é desfeita.
    """
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, StatusPedido.PENDENTE.value, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:
                raise EstoqueInsuficienteError(item["produto_id"])

            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
    return pedido_id


def _listar(where="", params=()):
    # Uma única query com JOIN no lugar das consultas por pedido/item (N+1).
    rows = get_db().execute(
        f"""
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        {where}
        ORDER BY p.id, i.id
        """,
        params,
    ).fetchall()

    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["id"]] = pedido
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos():
    return _listar()


def listar_por_usuario(usuario_id):
    return _listar("WHERE p.usuario_id = ?", (usuario_id,))


def buscar_status(pedido_id):
    row = get_db().execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return row["status"] if row else None


def atualizar_status(pedido_id, status_atual, novo_status):
    """Troca o status só se ele ainda for `status_atual`; no cancelamento devolve o estoque na mesma transação."""
    db = get_db()
    with db:
        cursor = db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ? AND status = ?",
            (novo_status, pedido_id, status_atual),
        )
        if cursor.rowcount == 0:
            raise StatusDesatualizadoError(pedido_id)

        if novo_status == StatusPedido.CANCELADO.value:
            db.execute(
                """
                UPDATE produtos
                SET estoque = estoque + (
                    SELECT COALESCE(SUM(i.quantidade), 0) FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )


def resumo_vendas():
    """Faturamento considera apenas pedidos não cancelados."""
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(CASE WHEN status <> :cancelado THEN total END), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status <> :cancelado THEN 1 ELSE 0 END), 0) AS pedidos_faturados,
               COALESCE(SUM(CASE WHEN status = :pendente THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = :aprovado THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = :cancelado THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        {
            "pendente": StatusPedido.PENDENTE.value,
            "aprovado": StatusPedido.APROVADO.value,
            "cancelado": StatusPedido.CANCELADO.value,
        },
    ).fetchone()
    return dict(row)
