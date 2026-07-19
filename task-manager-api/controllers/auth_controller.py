from flask import request, jsonify

from models.user import User
from middlewares.error_handler import ApiError
from middlewares.auth import generate_token


def login():
    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)

    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        raise ApiError('Email e senha são obrigatórios', 400)

    user = User.get_by_email(email)
    if not user or not user.check_password(password):
        raise ApiError('Credenciais inválidas', 401)
    if not user.active:
        raise ApiError('Usuário inativo', 403)

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user),
    }), 200
