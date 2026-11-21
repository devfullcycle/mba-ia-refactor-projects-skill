from flask import Flask

from routes.pedido_routes import criar_pedido_blueprint
from routes.produto_routes import criar_produto_blueprint
from routes.relatorio_routes import criar_relatorio_blueprint
from routes.sistema_routes import criar_sistema_blueprint
from routes.usuario_routes import criar_usuario_blueprint


def register_routes(app: Flask, controllers):
    app.register_blueprint(criar_produto_blueprint(controllers["produto"]))
    app.register_blueprint(criar_usuario_blueprint(controllers["usuario"]))
    app.register_blueprint(criar_pedido_blueprint(controllers["pedido"]))
    app.register_blueprint(criar_relatorio_blueprint(controllers["relatorio"]))
    app.register_blueprint(criar_sistema_blueprint(controllers["sistema"]))
