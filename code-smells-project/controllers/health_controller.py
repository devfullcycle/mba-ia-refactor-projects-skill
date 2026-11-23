from flask import jsonify
from models.database import check_connection
from config.settings import Config

class HealthController:
    @staticmethod
    def health_check():
        db_ok = check_connection()
        status_code = 200 if db_ok else 503

        return jsonify({
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "unreachable",
            "versao": "1.0.0",
            "ambiente": "development" if Config.DEBUG else "production",
            "debug": Config.DEBUG
        }), status_code

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
