import functools
import logging
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not installed — token auth middleware disabled. Run: pip install PyJWT")


def require_token(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not JWT_AVAILABLE:
            return f(*args, **kwargs)
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"erro": "Token de autenticação obrigatório"}), 401
        try:
            jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not JWT_AVAILABLE:
            return jsonify({"erro": "Autenticação não configurada (instale PyJWT)"}), 503
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"erro": "Token de autenticação obrigatório"}), 401
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            if payload.get("tipo") != "admin":
                return jsonify({"erro": "Acesso negado — requer perfil admin"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        return f(*args, **kwargs)
    return decorated
