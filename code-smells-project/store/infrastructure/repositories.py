"""Parameterized repositories and aggregate queries."""

from __future__ import annotations

import sqlite3

from store.domain.errors import ConflictError, IntegrityError, NotFoundError, ValidationError
from store.domain.models import OrderItemInput, ProductInput
from store.infrastructure.sqlite import SQLiteDatabase


def _product(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row["id"], "nome": row["nome"], "descricao": row["descricao"],
        "preco": row["preco"], "estoque": row["estoque"], "categoria": row["categoria"],
        "ativo": row["ativo"], "criado_em": row["criado_em"],
    }


def _user(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "senha": row["senha"], "tipo": row["tipo"], "criado_em": row["criado_em"]}


class ProductRepository:
    def __init__(self, database: SQLiteDatabase):
        self.database = database

    def list_all(self) -> list[dict]:
        with self.database.connection() as connection:
            return [_product(row) for row in connection.execute("SELECT * FROM produtos ORDER BY id").fetchall()]

    def get(self, product_id: int) -> dict | None:
        with self.database.connection() as connection:
            return _product(connection.execute("SELECT * FROM produtos WHERE id = ?", (product_id,)).fetchone())

    def create(self, value: ProductInput) -> int:
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    (value.nome, value.descricao, value.preco, value.estoque, value.categoria),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise IntegrityError("Produto inválido") from exc

    def update(self, product_id: int, value: ProductInput) -> None:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (value.nome, value.descricao, value.preco, value.estoque, value.categoria, product_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundError("Produto não encontrado")

    def delete(self, product_id: int) -> None:
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
                if cursor.rowcount == 0:
                    raise NotFoundError("Produto não encontrado")
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Produto possui itens de pedidos e não pode ser removido") from exc

    def search(self, term: str, category: str | None, price_min: float | None, price_max: float | None) -> list[dict]:
        clauses = ["1 = 1"]
        params: list[object] = []
        if term:
            clauses.append("(nome LIKE ? ESCAPE '\\' OR descricao LIKE ? ESCAPE '\\')")
            escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.extend((f"%{escaped}%", f"%{escaped}%"))
        if category:
            clauses.append("categoria = ?")
            params.append(category)
        if price_min is not None:
            clauses.append("preco >= ?")
            params.append(price_min)
        if price_max is not None:
            clauses.append("preco <= ?")
            params.append(price_max)
        query = f"SELECT * FROM produtos WHERE {' AND '.join(clauses)} ORDER BY id"
        with self.database.connection() as connection:
            return [_product(row) for row in connection.execute(query, params).fetchall()]


class UserRepository:
    def __init__(self, database: SQLiteDatabase):
        self.database = database

    def list_all(self) -> list[dict]:
        with self.database.connection() as connection:
            return [_user(row) for row in connection.execute("SELECT * FROM usuarios ORDER BY id").fetchall()]

    def get(self, user_id: int) -> dict | None:
        with self.database.connection() as connection:
            return _user(connection.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone())

    def get_by_email(self, email: str) -> dict | None:
        with self.database.connection() as connection:
            return _user(connection.execute("SELECT * FROM usuarios WHERE email = ? COLLATE NOCASE", (email,)).fetchone())

    def create(self, name: str, email: str, password_hash: str, role: str = "cliente") -> int:
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    (name, email, password_hash, role),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Email já cadastrado") from exc


class OrderRepository:
    def __init__(self, database: SQLiteDatabase):
        self.database = database

    def create(self, user_id: int, items: list[OrderItemInput]) -> dict:
        with self.database.transaction() as connection:
            if connection.execute("SELECT 1 FROM usuarios WHERE id = ?", (user_id,)).fetchone() is None:
                raise ValidationError("Usuário não encontrado")
            total = 0.0
            products: list[tuple[OrderItemInput, sqlite3.Row]] = []
            for item in items:
                product = connection.execute("SELECT * FROM produtos WHERE id = ?", (item.produto_id,)).fetchone()
                if product is None:
                    raise NotFoundError(f"Produto {item.produto_id} não encontrado")
                if product["estoque"] < item.quantidade:
                    raise ConflictError(f"Estoque insuficiente para {product['nome']}")
                total += float(product["preco"]) * item.quantidade
                products.append((item, product))

            order_cursor = connection.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (user_id, total),
            )
            order_id = int(order_cursor.lastrowid)
            for item, product in products:
                connection.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (order_id, item.produto_id, item.quantidade, product["preco"]),
                )
                stock_cursor = connection.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item.quantidade, item.produto_id, item.quantidade),
                )
                if stock_cursor.rowcount != 1:
                    raise ConflictError("Estoque insuficiente")
            return {"pedido_id": order_id, "total": total}

    def _list(self, user_id: int | None = None) -> list[dict]:
        query = """
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
        """
        params: tuple[object, ...] = ()
        if user_id is not None:
            query += " WHERE p.usuario_id = ?"
            params = (user_id,)
        query += " ORDER BY p.id, i.id"
        with self.database.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        grouped: dict[int, dict] = {}
        for row in rows:
            order = grouped.setdefault(row["id"], {
                "id": row["id"], "usuario_id": row["usuario_id"], "status": row["status"],
                "total": row["total"], "criado_em": row["criado_em"], "itens": [],
            })
            if row["produto_id"] is not None:
                order["itens"].append({
                    "produto_id": row["produto_id"], "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"], "preco_unitario": row["preco_unitario"],
                })
        return list(grouped.values())

    def list_for_user(self, user_id: int) -> list[dict]:
        return self._list(user_id)

    def list_all(self) -> list[dict]:
        return self._list()

    def update_status(self, order_id: int, status: str) -> None:
        with self.database.transaction() as connection:
            order = connection.execute("SELECT status FROM pedidos WHERE id = ?", (order_id,)).fetchone()
            if order is None:
                raise NotFoundError("Pedido não encontrado")
            previous = order["status"]
            if previous == "cancelado" and status != "cancelado":
                raise ConflictError("Pedido cancelado não pode voltar de status")
            if previous == status:
                return
            connection.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id))
            if status == "cancelado" and previous != "cancelado":
                connection.execute(
                    "UPDATE produtos SET estoque = estoque + (SELECT COALESCE(SUM(i.quantidade), 0) FROM itens_pedido i WHERE i.pedido_id = ? AND i.produto_id = produtos.id) WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)",
                    (order_id, order_id),
                )

    def report(self) -> dict:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(total), 0) AS gross,
                       SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pending,
                       SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS approved,
                       SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelled
                FROM pedidos
                """
            ).fetchone()
        gross = float(row["gross"] or 0)
        discount = gross * (0.1 if gross > 10000 else 0.05 if gross > 5000 else 0.02 if gross > 1000 else 0)
        return {
            "total_pedidos": row["total"], "faturamento_bruto": round(gross, 2),
            "desconto_aplicavel": round(discount, 2), "faturamento_liquido": round(gross - discount, 2),
            "pedidos_pendentes": row["pending"] or 0, "pedidos_aprovados": row["approved"] or 0,
            "pedidos_cancelados": row["cancelled"] or 0,
            "ticket_medio": round(gross / row["total"], 2) if row["total"] else 0,
        }
