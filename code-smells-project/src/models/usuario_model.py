"""Repositório de usuários. A senha nunca sai deste módulo nos dicts públicos."""
from typing import Optional

from .database import Database

TIPO_CLIENTE = "cliente"

_CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def _to_public_dict(row) -> dict:
    return {campo: row[campo] for campo in _CAMPOS_PUBLICOS}


class UsuarioModel:
    def __init__(self, db: Database):
        self.db = db

    def listar(self) -> list:
        rows = self.db.connection().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [_to_public_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id: int) -> Optional[dict]:
        row = self.db.connection().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _to_public_dict(row) if row else None

    def buscar_credenciais_por_email(self, email: str) -> list:
        """Retorna (usuario_publico, hash_senha) para cada usuário com o e-mail informado."""
        rows = self.db.connection().execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
        return [(_to_public_dict(row), row["senha"]) for row in rows]

    def criar(self, nome: str, email: str, senha_hash: str, tipo: str = TIPO_CLIENTE) -> int:
        conn = self.db.connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id: int, senha_hash: str) -> None:
        conn = self.db.connection()
        with conn:
            conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))

    def contar(self) -> int:
        return self.db.connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
