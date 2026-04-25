import logging
from flask import jsonify
from functools import wraps

logger = logging.getLogger(__name__)


def handle_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error("Erro nao tratado: %s", str(e), exc_info=True)
            return jsonify({"erro": "Erro interno do servidor"}), 500
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request
        import config.settings as settings

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != settings.ADMIN_TOKEN:
            return jsonify({"erro": "Acesso nao autorizado", "sucesso": False}), 401
        return f(*args, **kwargs)
    return decorated
