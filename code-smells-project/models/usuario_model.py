from .database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

class UsuarioModel:
    @staticmethod
    def _format_row(row, include_sensitive=False):
        if not row:
            return None
        data = {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        }
        if include_sensitive:
            data["senha"] = row["senha"]
        return data

    @classmethod
    def listar_todos(cls):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
        rows = cursor.fetchall()
        return [cls._format_row(row) for row in rows]

    @classmethod
    def buscar_por_id(cls, user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return cls._format_row(row)

    @classmethod
    def criar(cls, nome, email, senha, tipo="cliente"):
        db = get_db()
        cursor = db.cursor()
        senha_hash = generate_password_hash(senha)
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo)
        )
        db.commit()
        return cursor.lastrowid

    @classmethod
    def autenticar(cls, email, senha):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return None

        armazenada = row["senha"]
        valido = False

        # Suporte a hash seguro com fallback para senhas legadas pré-existentes
        if check_password_hash(armazenada, senha):
            valido = True
        elif armazenada == senha:
            # Senha legada em texto puro: autentica e atualiza para hash
            valido = True
            novo_hash = generate_password_hash(senha)
            cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (novo_hash, row["id"]))
            db.commit()

        if valido:
            return {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipo": row["tipo"]
            }
        return None

    @classmethod
    def contar(cls):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        return cursor.fetchone()[0]
