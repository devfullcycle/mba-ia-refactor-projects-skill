"""Configuração centralizada da aplicação.

Todos os valores sensíveis são lidos de variáveis de ambiente (ver `.env.example`).
Segredos não têm default fixo: quando `SECRET_KEY` não é informada, uma chave
aleatória é gerada em boot (tokens deixam de valer entre reinícios).
"""

import os
import secrets

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'tasks.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Autenticação default deny: escrita exige JWT por padrão. O middleware é
    # fail-closed e não usa esta flag para desativar a proteção; ela permanece
    # apenas para documentar/consultar a configuração efetiva.
    AUTH_REQUIRED = _as_bool(os.getenv('AUTH_REQUIRED'), default=True)
    JWT_EXPIRATION_SECONDS = int(os.getenv('JWT_EXPIRATION_SECONDS', '86400'))

    DEBUG = _as_bool(os.getenv('FLASK_DEBUG'), default=False)
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '5000'))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    AUTH_REQUIRED = True
