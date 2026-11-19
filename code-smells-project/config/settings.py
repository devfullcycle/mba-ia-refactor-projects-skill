import os
import secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Configuração central — tudo vem do ambiente, nada hardcoded."""

    # Se SECRET_KEY não for fornecida via ambiente, gera uma efêmera.
    # Nunca há um segredo conhecido embutido no código-fonte.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))

    # Permite expor utilitários administrativos destrutivos (ex.: reset-db).
    # Desligado por padrão — ligar só em ambiente de desenvolvimento.
    ADMIN_ENABLED = os.environ.get("ADMIN_ENABLED", "0") == "1"

    # Regra de negócio do relatório de vendas: (faturamento_mínimo, percentual).
    DESCONTO_FAIXAS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

    CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
    STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
