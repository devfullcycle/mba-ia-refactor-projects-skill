import pytest

from src.app import create_app
from src.config.settings import Config

SENHA_ADMIN = "admin-teste-123"
SENHA_CLIENTE = "cliente-teste-123"
ADMIN_TOKEN = "token-manutencao-teste"


@pytest.fixture
def app(tmp_path):
    class ConfigTeste(Config):
        APP_ENV = "teste"
        SECRET_KEY = "chave-de-teste"
        DB_PATH = str(tmp_path / "teste.db")
        SEED_DB = True
        SEED_ADMIN_PASSWORD = SENHA_ADMIN
        SEED_CLIENTE_PASSWORD = SENHA_CLIENTE
        CORS_ORIGINS = []

    ConfigTeste.ADMIN_TOKEN = ADMIN_TOKEN
    return create_app(ConfigTeste)


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email, senha):
    resposta = client.post("/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.get_json()
    corpo = resposta.get_json()
    return {"Authorization": f"Bearer {corpo['token']}"}, corpo["dados"]


@pytest.fixture
def admin(client):
    return _login(client, "admin@loja.com", SENHA_ADMIN)


@pytest.fixture
def joao(client):
    return _login(client, "joao@email.com", SENHA_CLIENTE)


@pytest.fixture
def maria(client):
    return _login(client, "maria@email.com", SENHA_CLIENTE)
