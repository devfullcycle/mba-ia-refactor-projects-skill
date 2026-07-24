"""Controller de metadados e health check.

O health check legado devolvia SECRET_KEY, caminho do banco, flag de debug e ambiente.
Aqui a resposta expõe apenas estado operacional.
"""


class HealthController:
    def __init__(self, produto_model, usuario_model, pedido_model, versao):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model
        self._versao = versao

    def index(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self._versao,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }, 200

    def health(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.count(),
                "usuarios": self._usuarios.count(),
                "pedidos": self._pedidos.count(),
            },
            "versao": self._versao,
        }, 200
