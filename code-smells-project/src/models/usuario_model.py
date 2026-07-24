"""Model de Usuário — acesso a dados, hash de senha e verificação de credenciais.

O hash nunca sai deste módulo: `CAMPOS_PUBLICOS` é a única forma serializada da entidade.
"""
from werkzeug.security import check_password_hash, generate_password_hash

from src.middlewares.error_handler import ConflictError, NotFoundError

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
TIPOS_VALIDOS = ("cliente", "admin")


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


class UsuarioModel:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    @property
    def _conn(self):
        return self._connection_provider()

    def list_all(self):
        rows = self._conn.execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios ORDER BY id"
        ).fetchall()
        return [_to_dict(row) for row in rows]

    def get(self, usuario_id):
        row = self._conn.execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return _to_dict(row) if row else None

    def get_or_fail(self, usuario_id):
        usuario = self.get(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def exists(self, usuario_id):
        row = self._conn.execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return row is not None

    def email_em_uso(self, email):
        row = self._conn.execute(
            "SELECT 1 FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return row is not None

    def create(self, nome, email, senha, tipo="cliente"):
        if self.email_em_uso(email):
            raise ConflictError("Email já cadastrado")

        connection = self._conn
        cursor = connection.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        connection.commit()
        return cursor.lastrowid

    def verify_credentials(self, email, senha):
        """Busca por e-mail e compara o hash na aplicação.

        O código legado comparava a senha dentro do WHERE, o que permitia bypass por
        SQL Injection.
        """
        row = self._conn.execute(
            "SELECT id, nome, email, tipo, criado_em, senha_hash FROM usuarios"
            " WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None or not check_password_hash(row["senha_hash"], senha):
            return None
        return _to_dict(row)

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
