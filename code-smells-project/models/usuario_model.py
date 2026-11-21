"""Acesso a dados de usuários. Campos de senha nunca saem desta camada para as respostas."""

COLUNAS_PUBLICAS = ("id", "nome", "email", "tipo", "criado_em")
SELECT_PUBLICO = "SELECT " + ", ".join(COLUNAS_PUBLICAS) + " FROM usuarios"


def usuario_to_public(row):
    return {coluna: row[coluna] for coluna in COLUNAS_PUBLICAS}


class UsuarioModel:
    def __init__(self, get_db):
        self._get_db = get_db

    def listar(self):
        rows = self._get_db().execute(SELECT_PUBLICO).fetchall()
        return [usuario_to_public(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._get_db().execute(SELECT_PUBLICO + " WHERE id = ?", (usuario_id,)).fetchone()
        return usuario_to_public(row) if row else None

    def buscar_credenciais_por_email(self, email):
        """Uso interno da autenticação: devolve (id, nome, email, tipo, senha armazenada)."""
        return self._get_db().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
        ).fetchall()

    def criar(self, nome, email, senha_hash, tipo):
        db = self._get_db()
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        db.commit()
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id, senha_hash):
        db = self._get_db()
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
        db.commit()
