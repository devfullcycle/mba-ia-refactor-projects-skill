"""Configurações centralizadas da aplicação Task Manager.

Segredos e parâmetros sensíveis via variáveis de ambiente (python-dotenv já
é dependência do projeto).
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

# Segredos e parâmetros sensíveis (via env)
SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///tasks.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# SMTP (deve vir de variáveis de ambiente em produção)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Constantes de domínio
VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
VALID_ROLES = ["user", "admin", "manager"]
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 6
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = "#000000"