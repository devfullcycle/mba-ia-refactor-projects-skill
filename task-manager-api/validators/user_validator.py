import re

from utils.constants import DEFAULT_ROLE, EMAIL_PATTERN, MIN_PASSWORD_LENGTH, USER_ROLES
from utils.errors import ValidationError


def _email(value):
    if not isinstance(value, str) or not re.match(EMAIL_PATTERN, value):
        raise ValidationError('Email inválido')
    return value


def _role(value):
    if not isinstance(value, str) or value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def _name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('Nome inválido')
    return value


def validate_create(data):
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    _email(email)
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    return {
        'name': _name(name),
        'email': email,
        'password': password,
        'role': _role(data.get('role', DEFAULT_ROLE)),
    }


def validate_update(data):
    fields = {}
    if 'name' in data:
        fields['name'] = _name(data['name'])
    if 'email' in data:
        fields['email'] = _email(data['email'])
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = password
    if 'role' in data:
        fields['role'] = _role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Credenciais inválidas')
    return email, password
