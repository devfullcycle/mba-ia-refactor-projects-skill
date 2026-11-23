import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from utils.errors import DatabaseError

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def init_db(app):
    """Liga o SQLAlchemy ao app e cria o schema (explicitamente, no boot)."""
    import models  # noqa: F401  (registra as tabelas)

    db.init_app(app)
    with app.app_context():
        db.create_all()


def commit_or_fail(message):
    """Commit com rollback, log da causa e erro de domínio com a mensagem da operação."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(message)
        raise DatabaseError(message)


def paginate(stmt, page=None):
    """Aplica (limit, offset) opcionais a um select; sem limit devolve o select intacto."""
    limit, offset = page or (None, 0)
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset:
        stmt = stmt.offset(offset)
    return stmt


def assign(entity, fields):
    """Copia campos já validados para a entidade."""
    for name, value in fields.items():
        setattr(entity, name, value)
