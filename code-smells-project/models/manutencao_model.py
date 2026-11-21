"""Operações de manutenção do banco e verificação de saúde."""

TABELAS_CONTAGEM = ("produtos", "usuarios", "pedidos")
TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class ManutencaoModel:
    def __init__(self, get_db):
        self._get_db = get_db

    def contagens(self):
        db = self._get_db()
        db.execute("SELECT 1")
        # nomes de tabela vêm de constantes internas, nunca da requisição
        return {tabela: db.execute("SELECT COUNT(*) FROM " + tabela).fetchone()[0] for tabela in TABELAS_CONTAGEM}

    def resetar(self):
        db = self._get_db()
        try:
            for tabela in TABELAS_RESET:
                db.execute("DELETE FROM " + tabela)
            db.commit()
        except Exception:
            db.rollback()
            raise
