class UsuarioModel:
    """Acesso a dados de usuários. Devolve o registro interno (inclui o hash da senha)."""

    def __init__(self, banco):
        self._banco = banco

    def listar(self):
        linhas = self._banco.conexao().execute(
            "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios ORDER BY id"
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        linha = self._banco.conexao().execute(
            "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return dict(linha) if linha else None

    def buscar_por_email(self, email):
        linhas = self._banco.conexao().execute(
            "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios WHERE email = ? ORDER BY id",
            (email,),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def existe_email(self, email):
        return self._banco.conexao().execute(
            "SELECT 1 FROM usuarios WHERE email = ? LIMIT 1", (email,)
        ).fetchone() is not None

    def criar(self, nome, email, senha_hash, tipo):
        conexao = self._banco.conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id, senha_hash):
        conexao = self._banco.conexao()
        with conexao:
            conexao.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
