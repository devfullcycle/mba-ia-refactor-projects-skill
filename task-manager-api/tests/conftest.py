import pytest

from src.app import create_app
from src.config.settings import Config

ADMIN_PASSWORD = "admin-teste-123"
USER_PASSWORD = "user-teste-123"
MANAGER_PASSWORD = "manager-teste-123"


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        APP_ENV = "test"
        SECRET_KEY = "chave-de-teste"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
        SEED_DB = True
        SEED_ADMIN_PASSWORD = ADMIN_PASSWORD
        SEED_USER_PASSWORD = USER_PASSWORD
        SEED_MANAGER_PASSWORD = MANAGER_PASSWORD
        SMTP_ENABLED = False
        CORS_ORIGINS = []

    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    return {"Authorization": f"Bearer {body['token']}"}, body["user"]


@pytest.fixture
def admin(client):
    return login(client, "joao@email.com", ADMIN_PASSWORD)


@pytest.fixture
def regular(client):
    return login(client, "maria@email.com", USER_PASSWORD)


@pytest.fixture
def manager(client):
    return login(client, "pedro@email.com", MANAGER_PASSWORD)
