from marshmallow import Schema, fields, validate, EXCLUDE

from utils.constants import VALID_ROLES, MIN_PASSWORD_LENGTH

_EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
_ROLE_MSG = 'Role inválido'
_EMAIL_MSG = 'Email inválido'


class UserCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True,
                      error_messages={'required': 'Nome é obrigatório', 'null': 'Nome é obrigatório'})
    email = fields.Str(
        required=True,
        error_messages={'required': 'Email é obrigatório', 'null': 'Email é obrigatório'},
        validate=validate.Regexp(_EMAIL_REGEX, error=_EMAIL_MSG),
    )
    password = fields.Str(
        required=True,
        error_messages={'required': 'Senha é obrigatória', 'null': 'Senha é obrigatória'},
        validate=validate.Length(min=MIN_PASSWORD_LENGTH,
                                 error='Senha deve ter no mínimo 4 caracteres'),
    )
    role = fields.Str(load_default='user',
                      validate=validate.OneOf(VALID_ROLES, error=_ROLE_MSG))


class UserUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str()
    email = fields.Str(validate=validate.Regexp(_EMAIL_REGEX, error=_EMAIL_MSG))
    password = fields.Str(validate=validate.Length(min=MIN_PASSWORD_LENGTH, error='Senha muito curta'))
    role = fields.Str(validate=validate.OneOf(VALID_ROLES, error=_ROLE_MSG))
    active = fields.Bool()


class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Str(required=True)
    password = fields.Str(required=True)
