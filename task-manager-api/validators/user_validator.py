from utils.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES
from utils.errors import ValidationError
from validators import common

_ACTIVE_MESSAGE = 'Campo active deve ser booleano'


def _role(value):
    if not isinstance(value, str) or value not in USER_ROLES:
        raise ValidationError('Role inválido')
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
    fields = {
        'name': common.name(name),
        'email': common.email(email),
        'password': common.password(password),
        'role': _role(data.get('role', DEFAULT_ROLE)),
    }
    if 'active' in data:  # campo privilegiado: aceito aqui, autorizado no controller
        fields['active'] = common.boolean(data['active'], _ACTIVE_MESSAGE)
    return fields


def validate_update(data):
    fields = {}
    if 'name' in data:
        fields['name'] = common.name(data['name'])
    if 'email' in data:
        fields['email'] = common.email(data['email'])
    if 'password' in data:
        fields['password'] = common.password(
            data['password'], f'Senha muito curta (mínimo {MIN_PASSWORD_LENGTH} caracteres)')
    if 'role' in data:
        fields['role'] = _role(data['role'])
    if 'active' in data:
        fields['active'] = common.boolean(data['active'], _ACTIVE_MESSAGE)
    return fields


def validate_login(data):
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Credenciais inválidas')
    return email.strip().lower(), password
