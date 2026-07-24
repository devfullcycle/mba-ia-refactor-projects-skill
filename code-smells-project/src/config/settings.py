"""Configuração da aplicação.

Toda origem de valor é variável de ambiente — nenhum segredo literal neste módulo.
Ver `.env.example` para a lista completa de chaves.
"""
import os
import secrets

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida — impede o boot de forma explícita."""


def _bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Configuração resolvida a partir do ambiente no momento da criação da app."""

    def __init__(self, env=None):
        self.ENV = env or os.environ.get("APP_ENV", "development")
        # Debug é sempre opt-in explícito: o debugger do Werkzeug permite execução
        # remota de código, então nunca é ligado por default (nem em desenvolvimento).
        self.DEBUG = _bool("FLASK_DEBUG", default=False)
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
        self.CORS_ORIGINS = [
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        # Dados de demonstração não são semeados em produção.
        self.SEED_ON_INIT = _bool("SEED_ON_INIT", default=self.ENV != "production")
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
                "SECRET_KEY é obrigatória em produção. Defina a variável de ambiente "
                "(ver .env.example) antes de iniciar a aplicação."
            )
        # Em desenvolvimento, gera uma chave efêmera em vez de embutir um valor no código.
        self.SECRET_KEY_IS_EPHEMERAL = True
        return secrets.token_hex(32)

    def as_flask_config(self):
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "DEBUG": self.DEBUG,
            "DATABASE_PATH": self.DATABASE_PATH,
            "APP_VERSION": self.APP_VERSION,
            "ENV_NAME": self.ENV,
        }
