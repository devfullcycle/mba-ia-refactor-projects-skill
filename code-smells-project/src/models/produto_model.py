from src.config.database import get_db
from src.models.base import row_to_dict

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")

# Produtos excluídos ficam inativos (preserva o histórico de pedidos) e somem das consultas.
SOMENTE_ATIVOS = "ativo = 1"


def _to_dict(row):
    return row_to_dict(row, CAMPOS)


def listar():
    rows = get_db().execute(f"SELECT * FROM produtos WHERE {SOMENTE_ATIVOS}").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute(
        f"SELECT * FROM produtos WHERE id = ? AND {SOMENTE_ATIVOS}", (produto_id,)
    ).fetchone()
    return _to_dict(row) if row else None


def buscar_por_ids(produto_ids):
    if not produto_ids:
        return {}
    placeholders = ", ".join("?" for _ in produto_ids)
    rows = get_db().execute(
        f"SELECT * FROM produtos WHERE id IN ({placeholders}) AND {SOMENTE_ATIVOS}", tuple(produto_ids)
    ).fetchall()
    return {row["id"]: _to_dict(row) for row in rows}


def _escapar_like(termo):
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    query = f"SELECT * FROM produtos WHERE {SOMENTE_ATIVOS}"
    params = []
    if termo:
        padrao = f"%{_escapar_like(termo)}%"
        query += " AND (nome LIKE ? ESCAPE '\\' OR descricao LIKE ? ESCAPE '\\')"
        params.extend([padrao, padrao])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    rows = get_db().execute(query, params).fetchall()
    return [_to_dict(row) for row in rows]


def contar():
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def desativar(produto_id):
    db = get_db()
    with db:
        db.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))
