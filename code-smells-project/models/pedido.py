from database import db
from datetime import datetime

class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    produto = db.relationship('Produto')

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(50), default='pendente')
    total = db.Column(db.Float, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "status": self.status,
            "total": self.total,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "itens": [
                {
                    "produto_id": item.produto_id,
                    "produto_nome": item.produto.nome if item.produto else "Desconhecido",
                    "quantidade": item.quantidade,
                    "preco_unitario": item.preco_unitario
                } for item in self.itens
            ]
        }
