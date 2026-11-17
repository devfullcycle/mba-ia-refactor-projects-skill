from flask import jsonify
from models.produto_model import ProdutoModel
from models.usuario_model import UsuarioModel
from models.pedido_model import PedidoModel
from config.settings import Config

class HealthController:
    @staticmethod
    def health_check():
        produtos_total = ProdutoModel.contar()
        usuarios_total = UsuarioModel.contar()
        pedidos_total = PedidoModel.contar()

        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos_total,
                "usuarios": usuarios_total,
                "pedidos": pedidos_total
            },
            "versao": "1.0.0",
            "ambiente": "development" if Config.DEBUG else "production",
            "debug": Config.DEBUG
        }), 200

    @staticmethod
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        }), 200
