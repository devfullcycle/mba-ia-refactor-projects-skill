"""Configuração central da aplicação — segredos via ambiente, nunca hardcoded."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class Config:
    # Segredo de assinatura de sessão/token — obrigatório vir do ambiente em produção.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')

    # Path absoluto e determinístico do SQLite — evita seed/app gravarem em arquivos
    # diferentes conforme o cwd/instance_path do flask-sqlalchemy.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI', f'sqlite:///{BASE_DIR / "tasks.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # debug controlado por ambiente (nunca ligado por padrão).
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5000'))

    # Credenciais de e-mail para notificações — via ambiente.
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
