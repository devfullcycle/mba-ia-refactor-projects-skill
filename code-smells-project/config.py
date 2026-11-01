"""Configuração centralizada — lida de variáveis de ambiente.

Resolve QUAL-07 (config hardcoded) e SEC-02 (segredo no código).
Segredos não têm default: a aplicação falha explicitamente se ausentes.
"""

import os


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # Segredo obrigatório em runtime; em testes pode ser injetado.
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Validade do token de sessão emitido no login (padrão: 8 horas).
    TOKEN_MAX_AGE_SECONDS = int(os.getenv("TOKEN_MAX_AGE_SECONDS", "28800"))

    DEBUG = _as_bool(os.getenv("FLASK_DEBUG"), default=False)

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")

    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Níveis de usuário (coluna `usuarios.tipo` no seed)
    PERFIL_ADMIN = "admin"
    PERFIL_CLIENTE = "cliente"

    # Valores de domínio antes espalhados no código (controllers.py / models.py)
    CATEGORIAS_VALIDAS = (
        "informatica",
        "moveis",
        "vestuario",
        "geral",
        "eletronicos",
        "livros",
    )
    STATUS_PEDIDO_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

    NOME_PRODUTO_MIN = 2
    NOME_PRODUTO_MAX = 200

    # Faixas de desconto do relatório de vendas: (faturamento_mínimo, percentual)
    FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

    @classmethod
    def database_url(cls):
        return cls.DATABASE_PATH


def require_secret_key(app):
    """Garante SECRET_KEY presente no boot, sem nunca ter default literal."""
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY não definida. Configure a variável de ambiente SECRET_KEY "
            "(veja .env.example)."
        )
