"""Model de Usuário: persistência, hashing de senha e serialização pública."""
from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"

# Nunca inclui a senha: é a única forma de um usuário sair do model.
_CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
_CAMPOS_SESSAO = ("id", "nome", "email", "tipo")


def _to_public_dict(row, campos=_CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


class UsuarioModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def listar(self):
        rows = self._conn().execute("SELECT * FROM usuarios").fetchall()
        return [_to_public_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._conn().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _to_public_dict(row) if row else None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        conn.commit()
        return cursor.lastrowid

    def autenticar(self, email, senha):
        """Retorna os dados públicos do usuário se as credenciais forem válidas, senão None."""
        row = self._conn().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if row and row["senha"] and check_password_hash(row["senha"], senha):
            return _to_public_dict(row, _CAMPOS_SESSAO)
        return None

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
