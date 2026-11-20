"""Repositório de pedidos: criação atômica e listagem sem N+1."""
from collections import defaultdict
from typing import Optional

from .database import Database

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO)

PRODUTO_DESCONHECIDO = "Desconhecido"


class EstoqueInsuficienteError(Exception):
    def __init__(self, produto_id: int):
        super().__init__(f"Estoque insuficiente para o produto {produto_id}")
        self.produto_id = produto_id


class PedidoModel:
    def __init__(self, db: Database):
        self.db = db

    def criar(self, usuario_id: int, total: float, itens: list) -> int:
        """Cria pedido, itens e baixa de estoque em uma única transação.

        `itens` é uma lista de dicts com produto_id, quantidade e preco_unitario.
        Lança EstoqueInsuficienteError (com rollback) se a baixa condicional falhar.
        """
        conn = self.db.connection()
        with conn:
            pedido_id = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid
            for item in itens:
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
                atualizado = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if atualizado == 0:
                    raise EstoqueInsuficienteError(item["produto_id"])
        return pedido_id

    def _listar(self, usuario_id: Optional[int] = None) -> list:
        conn = self.db.connection()
        filtro, params = ("WHERE usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())
        pedidos = conn.execute(f"SELECT * FROM pedidos {filtro} ORDER BY id", params).fetchall()
        if not pedidos:
            return []

        ids = [pedido["id"] for pedido in pedidos]
        placeholders = ", ".join("?" for _ in ids)
        itens = conn.execute(
            f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
                   COALESCE(p.nome, ?) AS produto_nome
            FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            ORDER BY i.id
            """,
            (PRODUTO_DESCONHECIDO, *ids),
        ).fetchall()

        itens_por_pedido = defaultdict(list)
        for item in itens:
            itens_por_pedido[item["pedido_id"]].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })

        return [
            {
                "id": pedido["id"],
                "usuario_id": pedido["usuario_id"],
                "status": pedido["status"],
                "total": pedido["total"],
                "criado_em": pedido["criado_em"],
                "itens": itens_por_pedido[pedido["id"]],
            }
            for pedido in pedidos
        ]

    def listar_todos(self) -> list:
        return self._listar()

    def listar_por_usuario(self, usuario_id: int) -> list:
        return self._listar(usuario_id)

    def existe(self, pedido_id: int) -> bool:
        return self.db.connection().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None

    def atualizar_status(self, pedido_id: int, status: str) -> None:
        conn = self.db.connection()
        with conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def contar(self) -> int:
        return self.db.connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
