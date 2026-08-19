from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_db():
    return db.session

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Register models here to ensure they are created
        from models.produto import Produto
        from models.usuario import Usuario
        from models.pedido import Pedido, ItemPedido
        db.create_all()
