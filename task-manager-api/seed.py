"""Adapter CLI para substituir todos os dados por fixtures de desenvolvimento."""

from __future__ import annotations

import os

from app import create_app
from database import db


def seed_data(config_overrides=None, after_stage=None):
    app = create_app(config_overrides)
    passwords = {
        "admin": os.getenv("TASK_MANAGER_SEED_ADMIN_PASSWORD"),
        "user": os.getenv("TASK_MANAGER_SEED_USER_PASSWORD"),
        "manager": os.getenv("TASK_MANAGER_SEED_MANAGER_PASSWORD"),
    }
    with app.app_context():
        db.create_all()
        counts = app.extensions["controllers"]["seed"].seed(
            passwords,
            after_stage=after_stage,
        )
    print("Seed concluído com sucesso!")
    print(f"  {counts['users']} usuários")
    print(f"  {counts['categories']} categorias")
    print(f"  {counts['tasks']} tasks")
    return counts


if __name__ == "__main__":
    seed_data()
