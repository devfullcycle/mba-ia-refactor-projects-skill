"""Configuração central: único módulo que lê variáveis de ambiente."""
import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


DEV_SECRET_KEY = 'dev-only-insecure-key-change-me'

SECRET_KEY = os.getenv('SECRET_KEY', DEV_SECRET_KEY)
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

DEBUG = _env_bool('DEBUG', False)
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '5000'))

# Lista separada por vírgulas; '*' libera todas as origens (padrão de desenvolvimento).
CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', '*').split(',') if o.strip()]

# Validade do token de login, em segundos.
TOKEN_MAX_AGE = int(os.getenv('TOKEN_MAX_AGE', '86400'))

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
