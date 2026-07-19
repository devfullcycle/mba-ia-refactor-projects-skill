from marshmallow import Schema, fields, validate, EXCLUDE

from utils.constants import (
    VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH,
    MIN_PRIORITY, MAX_PRIORITY, DEFAULT_PRIORITY,
)

_PRIORITY_MSG = 'Prioridade deve ser entre 1 e 5'
_STATUS_MSG = 'Status inválido'


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        required=True,
        error_messages={'required': 'Título é obrigatório', 'null': 'Título é obrigatório'},
        validate=[
            validate.Length(min=MIN_TITLE_LENGTH, error='Título muito curto'),
            validate.Length(max=MAX_TITLE_LENGTH, error='Título muito longo'),
        ],
    )
    description = fields.Str(load_default='')
    status = fields.Str(load_default='pending',
                        validate=validate.OneOf(VALID_STATUSES, error=_STATUS_MSG))
    priority = fields.Int(load_default=DEFAULT_PRIORITY,
                          validate=validate.Range(min=MIN_PRIORITY, max=MAX_PRIORITY, error=_PRIORITY_MSG))
    user_id = fields.Int(load_default=None, allow_none=True)
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Str(load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)


class TaskUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(validate=[
        validate.Length(min=MIN_TITLE_LENGTH, error='Título muito curto'),
        validate.Length(max=MAX_TITLE_LENGTH, error='Título muito longo'),
    ])
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(VALID_STATUSES, error=_STATUS_MSG))
    priority = fields.Int(validate=validate.Range(min=MIN_PRIORITY, max=MAX_PRIORITY, error=_PRIORITY_MSG))
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    due_date = fields.Str(allow_none=True)
    tags = fields.Raw(allow_none=True)
