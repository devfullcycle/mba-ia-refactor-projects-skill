import logging
from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError

from utils.errors import AppError

logger = logging.getLogger(__name__)


@contextmanager
def persistence_errors(message):
    """Converte falhas de persistência em AppError(500) com a mensagem da operação."""
    try:
        yield
    except SQLAlchemyError:
        logger.exception(message)
        raise AppError(message, 500)


def get_or_404(model, entity_id, message):
    """Busca por id; id inválido ou inexistente resulta em 404 com `message`."""
    try:
        entity_id = int(entity_id)
    except (ValueError, TypeError):
        raise AppError(message, 404)
    entity = model.find(entity_id)
    if entity is None:
        raise AppError(message, 404)
    return entity
