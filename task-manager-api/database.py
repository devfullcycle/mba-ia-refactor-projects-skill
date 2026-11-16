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
