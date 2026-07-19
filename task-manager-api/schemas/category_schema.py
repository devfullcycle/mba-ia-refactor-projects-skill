from marshmallow import Schema, fields, EXCLUDE

from utils.constants import DEFAULT_COLOR


class CategoryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True,
                      error_messages={'required': 'Nome é obrigatório', 'null': 'Nome é obrigatório'})
    description = fields.Str(load_default='')
    color = fields.Str(load_default=DEFAULT_COLOR)


class CategoryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str()
    description = fields.Str()
    color = fields.Str()
