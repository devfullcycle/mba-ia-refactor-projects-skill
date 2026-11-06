"""Configuração da aplicação lida do ambiente (nenhum segredo literal no código)."""
import os

APP_VERSAO = "1.0.0"


def _bool(valor, padrao):
    if valor is None or valor.strip() == "":
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "sim")


class Settings:
    def __init__(self, ambiente=None):
        env = os.environ if ambiente is None else ambiente
        self.debug = _bool(env.get("APP_DEBUG"), False)
        self.host = env.get("APP_HOST", "127.0.0.1")
        self.port = int(env.get("APP_PORT", "5000"))
        self.ambiente = env.get("APP_ENV", "producao")
        self.db_path = env.get("DB_PATH", "loja.db")
        # Sem SECRET_KEY definida, app.py gera uma chave aleatória por processo (tokens expiram ao reiniciar).
        self.secret_key = env.get("SECRET_KEY") or None
        self.token_max_age = int(env.get("TOKEN_MAX_AGE", "3600"))
        self.cors_origins = [o.strip() for o in env.get("CORS_ORIGINS", "").split(",") if o.strip()]
        # Senhas do seed de usuários: sem valor padrão; sem a variável, o usuário não é semeado.
        self.seed_admin_password = env.get("SEED_ADMIN_PASSWORD") or None
        self.seed_cliente_password = env.get("SEED_CLIENTE_PASSWORD") or None
        self.allow_destructive = _bool(env.get("ALLOW_DESTRUCTIVE"), False)
        self.log_level = env.get("LOG_LEVEL", "INFO").upper()
