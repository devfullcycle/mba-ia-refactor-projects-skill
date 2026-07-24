"""Ponto de entrada do servidor de desenvolvimento.

Uso: python run.py
Configuração via variáveis de ambiente — ver `.env.example`.
"""
from src.app import create_app
from src.config.settings import Config

config = Config()
app = create_app(config)

if __name__ == "__main__":
    app.logger.info(
        "Servidor iniciado em http://%s:%s (ambiente: %s)",
        config.HOST,
        config.PORT,
        config.ENV,
    )
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
