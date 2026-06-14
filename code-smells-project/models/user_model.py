from werkzeug.security import generate_password_hash, check_password_hash


class UserModel:
    def __init__(self, db):
        self.db = db

    def find_all(self):
        rows = self.db.execute("SELECT * FROM usuarios").fetchall()
        return [self._to_dict(row) for row in rows]

    def find_by_id(self, user_id):
        row = self.db.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return self._to_dict(row) if row else None

    def find_by_email(self, email):
        return self.db.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()

    def create(self, nome, email, senha, tipo="cliente"):
        password_hash = generate_password_hash(senha)
        cursor = self.db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, password_hash, tipo),
        )
        self.db.commit()
        return cursor.lastrowid

    def authenticate(self, email, senha):
        row = self.find_by_email(email)
        if row and check_password_hash(row["senha"], senha):
            return self._to_dict(row)
        return None

    def _to_dict(self, row):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"],
        }
