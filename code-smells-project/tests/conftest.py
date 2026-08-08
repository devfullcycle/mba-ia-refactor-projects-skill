"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from src.app import create_app
from src.config.settings import Settings
from src.db.database import init_db


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(
        secret_key="test-secret",
        debug=False,
        host="127.0.0.1",
        port=5003,
        db_path=str(tmp_path / "test.db"),
        ambiente="teste",
        admin_token="test-admin-token",
    )


@pytest.fixture()
def app(settings: Settings):
    init_db(settings)
    application = create_app(settings)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
