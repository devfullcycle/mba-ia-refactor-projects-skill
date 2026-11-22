from database import db


class CrudMixin:
    """Persistência básica compartilhada pelos models.

    Em falha, o rollback é feito e a exceção do SQLAlchemy é propagada; quem
    orquestra (controller) decide a mensagem de erro para o cliente.
    """

    @classmethod
    def find(cls, entity_id):
        return db.session.get(cls, entity_id)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
