"""Configuração central da aplicação — segredos via ambiente (nunca hardcoded)."""
import os
import secrets

# Segredo carregado do ambiente; em dev, gera um valor aleatório (não fica fixo no código).
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Debug controlado por ambiente; desligado por padrão (nunca ligado em produção).
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Caminho do banco e servidor.
DB_PATH = os.environ.get("DB_PATH", "loja.db")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
AMBIENTE = os.environ.get("AMBIENTE", "producao")

# Token exigido para operações administrativas destrutivas (vazio => bloqueado por padrão).
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# Regras de negócio — faixas de desconto do relatório de vendas (maior faixa primeiro).
DESCONTO_FAIXAS = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
