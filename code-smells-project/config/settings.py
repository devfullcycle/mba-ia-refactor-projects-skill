"""Configuração central: único lugar que lê variáveis de ambiente."""
import os
import secrets


def _env_bool(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# Sem default fixo no código: se SECRET_KEY não for definida, gera uma chave
# aleatória para o processo (a aplicação não usa sessões assinadas hoje).
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
DEBUG = _env_bool("DEBUG")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DB_PATH = os.getenv("DB_PATH", "loja.db")
APP_VERSION = "1.0.0"
APP_ENV = os.getenv("APP_ENV", "producao")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# Token exigido nas rotas /admin/*. Sem token configurado, as rotas ficam desabilitadas.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
