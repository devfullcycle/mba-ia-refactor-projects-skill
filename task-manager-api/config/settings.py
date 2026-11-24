"""Configuração central: único módulo que lê variáveis de ambiente."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


# Sem SECRET_KEY no ambiente, gera uma chave aleatória por processo: nunca há chave
# conhecida no código (tokens forjáveis); o custo é invalidar os tokens a cada restart.
SECRET_KEY_FROM_ENV = bool(os.getenv('SECRET_KEY'))
SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(48)
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

DEBUG = _env_bool('DEBUG', False)
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '5000'))

# Lista separada por vírgulas; '*' libera todas as origens (padrão de desenvolvimento).
# Em produção, defina as origens permitidas explicitamente.
CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', '*').split(',') if o.strip()]

# Validade do token de login, em segundos.
TOKEN_MAX_AGE = int(os.getenv('TOKEN_MAX_AGE', '86400'))

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# Senha usada pelo seed.py para todos os usuários de exemplo; vazia = senhas aleatórias.
SEED_PASSWORD = os.getenv('SEED_PASSWORD', '')
