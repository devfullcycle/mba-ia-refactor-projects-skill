from werkzeug.security import generate_password_hash, check_password_hash


class UsuarioModel:
    """Acesso a dados de usuários. Nunca serializa a senha."""

    def __init__(self, conn):
        self._conn = conn

    @staticmethod
    def _serialize(row):
        # A senha (hash) é intencionalmente omitida da serialização pública.
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"],
        }

    def list(self):
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        return [self._serialize(r) for r in cursor.fetchall()]

    def get(self, usuario_id):
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        return self._serialize(row) if row else None

    def create(self, nome, email, senha, tipo="cliente"):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        self._conn.commit()
        return cursor.lastrowid

    def authenticate(self, email, senha):
        """Valida credenciais comparando contra o hash armazenado."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row and check_password_hash(row["senha"], senha):
            return self._serialize(row)
        return None
