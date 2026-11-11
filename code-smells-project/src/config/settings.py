import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto (code-smells-project/): caminhos relativos não dependem mais do diretório de execução.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

AMBIENTE_PRODUCAO = "producao"


def _env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


def _env_lista(nome):
    valor = os.getenv(nome, "")
    return [item.strip() for item in valor.split(",") if item.strip()]


def _resolver_caminho(valor):
    caminho = Path(valor)
    return str(caminho if caminho.is_absolute() else PROJECT_ROOT / caminho)


class Config:
    APP_VERSION = "1.1.0"
    APP_ENV = os.getenv("APP_ENV", AMBIENTE_PRODUCAO)

    SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN_TTL_SEGUNDOS = int(os.getenv("TOKEN_TTL_SEGUNDOS", "3600"))
    DEBUG = _env_bool("DEBUG", False)
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Vazio = CORS desabilitado (apenas mesma origem).
    CORS_ORIGINS = _env_lista("CORS_ORIGINS")

    DB_PATH = _resolver_caminho(os.getenv("DB_PATH", "loja.db"))

    # Seed é opt-in e nunca roda em produção; senhas não informadas são geradas aleatoriamente.
    SEED_DB = _env_bool("SEED_DB", False)
    SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD") or None
    SEED_CLIENTE_PASSWORD = os.getenv("SEED_CLIENTE_PASSWORD") or None

    # Endpoints /admin/* ficam desabilitados enquanto ADMIN_TOKEN não for definido.
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

    @classmethod
    def em_producao(cls):
        return cls.APP_ENV == AMBIENTE_PRODUCAO

    @classmethod
    def validar(cls):
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = secrets.token_hex(32)
            logger.warning(
                "SECRET_KEY não definida; usando chave aleatória temporária "
                "(tokens de login deixam de valer ao reiniciar o processo)."
            )
