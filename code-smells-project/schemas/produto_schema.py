from marshmallow import Schema, fields, validate


class ProdutoSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    descricao = fields.Str(load_default="")
    preco = fields.Float(required=True, validate=validate.Range(min=0))
    estoque = fields.Int(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(load_default="geral")
