import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


class Config:
    APP_VERSION = "1.0.0"
    APP_ENV = os.getenv("APP_ENV", "producao")

    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = _env_bool("DEBUG", False)
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DB_PATH = os.getenv("DB_PATH", "loja.db")
    SEED_DB = _env_bool("SEED_DB", True)
    SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    # Endpoints /admin/* ficam desabilitados enquanto ADMIN_TOKEN não for definido.
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

    @classmethod
    def validar(cls):
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = secrets.token_hex(32)
            logger.warning("SECRET_KEY não definida; usando chave aleatória temporária para este processo.")
