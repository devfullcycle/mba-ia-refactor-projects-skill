def register_routes(app, produto_ctrl, usuario_ctrl, pedido_ctrl, sistema_ctrl):
    """Camada de roteamento HTTP — delega imediatamente aos controllers.

    Mantém exatamente os mesmos paths, métodos e nomes do projeto original.
    """

    # Produtos
    app.add_url_rule("/produtos", "listar_produtos", produto_ctrl.listar, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", produto_ctrl.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_ctrl.buscar, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", produto_ctrl.criar, methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_ctrl.atualizar, methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_ctrl.deletar, methods=["DELETE"])

    # Usuários
    app.add_url_rule("/usuarios", "listar_usuarios", usuario_ctrl.listar, methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_ctrl.buscar, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuario_ctrl.criar, methods=["POST"])
    app.add_url_rule("/login", "login", usuario_ctrl.login, methods=["POST"])

    # Pedidos
    app.add_url_rule("/pedidos", "criar_pedido", pedido_ctrl.criar, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_ctrl.listar_todos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_ctrl.listar_por_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_ctrl.atualizar_status, methods=["PUT"])

    # Sistema
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", sistema_ctrl.relatorio_vendas, methods=["GET"])
    app.add_url_rule("/health", "health_check", sistema_ctrl.health_check, methods=["GET"])
    app.add_url_rule("/", "index", sistema_ctrl.index, methods=["GET"])
    app.add_url_rule("/admin/reset-db", "reset_database", sistema_ctrl.reset_db, methods=["POST"])
