from flask import request
from core.db import get_db


def index():
    return (
        {
            "mensagem": "Bem-vindo a API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        },
        200,
    )


def health_check():
    db = get_db()
    produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    return (
        {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos,
                "usuarios": usuarios,
                "pedidos": pedidos,
            },
            "versao": "1.0.0",
        },
        200,
    )


def reset_database():
    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def executar_query():
    data = request.get_json() or {}
    query = data.get("sql", "")
    if not query:
        return {"erro": "Query nao informada"}, 400
    if not query.strip().upper().startswith("SELECT"):
        return {"erro": "Apenas consultas SELECT sao permitidas"}, 403

    db = get_db()
    rows = db.execute(query).fetchall()
    result = [dict(row) for row in rows]
    return {"dados": result, "sucesso": True}, 200
