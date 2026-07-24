"""Configuração da aplicação — toda origem é variável de ambiente.

Ver `.env.example`. Nenhum segredo literal neste módulo.
"""
import os
import secrets


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida — impede o boot de forma explícita."""


def _bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Config:
    def __init__(self, env=None):
        self.ENV = env or os.environ.get("APP_ENV", "development")
        # Debug é opt-in explícito: o debugger do Werkzeug expõe execução de código.
        self.DEBUG = _bool("FLASK_DEBUG", default=False)
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.APP_VERSION = os.environ.get("APP_VERSION", "1.0")

        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URI", "sqlite:///tasks.db"
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        self.CORS_ORIGINS = [
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]

        self.PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "8"))
        self.TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))

        # Credenciais de e-mail vêm do ambiente; sem elas, as notificações vão para o log.
        self.SMTP = {
            "host": os.environ.get("SMTP_HOST"),
            "port": os.environ.get("SMTP_PORT", "587"),
            "user": os.environ.get("SMTP_USER"),
            "password": os.environ.get("SMTP_PASSWORD"),
        }

        self.SECRET_KEY_IS_EPHEMERAL = False
        self.SECRET_KEY = self._resolve_secret_key()

    @property
    def is_production(self):
        return self.ENV == "production"

    def _resolve_secret_key(self):
        secret = os.environ.get("SECRET_KEY")
        if secret:
            return secret
        if self.ENV == "production":
            raise ConfigError(
                "SECRET_KEY é obrigatória em produção — os tokens de sessão são assinados "
                "com ela. Defina a variável de ambiente (ver .env.example)."
            )
        # Em desenvolvimento, chave efêmera em vez de segredo embutido no código.
        self.SECRET_KEY_IS_EPHEMERAL = True
        return secrets.token_hex(32)

    def as_flask_config(self):
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "DEBUG": self.DEBUG,
            "SQLALCHEMY_DATABASE_URI": self.SQLALCHEMY_DATABASE_URI,
            "SQLALCHEMY_TRACK_MODIFICATIONS": self.SQLALCHEMY_TRACK_MODIFICATIONS,
            "APP_VERSION": self.APP_VERSION,
            "TOKEN_TTL_SECONDS": self.TOKEN_TTL_SECONDS,
            "PASSWORD_MIN_LENGTH": self.PASSWORD_MIN_LENGTH,
            "ENV_NAME": self.ENV,
        }
