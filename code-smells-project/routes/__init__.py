from routes import produto, usuario, pedido, sistema

def register_blueprints(app):
    app.register_blueprint(produto.bp)
    app.register_blueprint(usuario.bp)
    app.register_blueprint(pedido.bp)
    app.register_blueprint(sistema.bp)
