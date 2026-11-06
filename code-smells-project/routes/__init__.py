from routes import pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes


def registrar_rotas(app):
    for modulo in (sistema_routes, produto_routes, usuario_routes, pedido_routes, relatorio_routes):
        app.register_blueprint(modulo.bp)
