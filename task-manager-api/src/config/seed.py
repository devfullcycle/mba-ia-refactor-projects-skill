"""Dados de exemplo. Idempotente: só popula um banco vazio, a menos que reset=True."""
import logging
import secrets
from datetime import timedelta

from flask import current_app

from src.config.database import db
from src.models import Category, Task, User
from src.models import user as user_model
from src.utils.dates import utc_now

logger = logging.getLogger(__name__)

GENERATED_PASSWORD_BYTES = 12

USERS = (
    {"name": "João Silva", "email": "joao@email.com", "role": user_model.ROLE_ADMIN, "password_key": "SEED_ADMIN_PASSWORD"},
    {"name": "Maria Santos", "email": "maria@email.com", "role": user_model.ROLE_USER, "password_key": "SEED_USER_PASSWORD"},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "role": user_model.ROLE_MANAGER, "password_key": "SEED_MANAGER_PASSWORD"},
)

CATEGORIES = (
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
)

# (título, descrição, status, prioridade, índice do usuário, índice da categoria, dias até o prazo, tags)
TASKS = (
    ("Implementar autenticação JWT", "Adicionar autenticação real com JWT", "pending", 1, 0, 0, -3, None),
    ("Criar tela de login", "Tela de login responsiva", "in_progress", 2, 1, 1, 5, None),
    ("Configurar CI/CD", "Pipeline com GitHub Actions", "done", 2, 2, 2, None, "devops,ci,github"),
    ("Corrigir bug no filtro de busca", "Filtro não funciona com caracteres especiais", "pending", 1, 0, 3, -1, None),
    ("Adicionar paginação na API", "Endpoints retornam todos os registros", "pending", 3, 0, 0, 10, None),
    ("Escrever testes unitários", "Cobertura mínima de 80%", "pending", 2, 1, 0, None, None),
    ("Documentar API com Swagger", "Gerar documentação automática", "cancelled", 4, 2, 0, None, None),
    ("Refatorar models", "Melhorar organização dos models", "in_progress", 3, 1, 0, None, "refactor,tech-debt"),
    ("Configurar monitoramento", "Prometheus + Grafana", "pending", 4, 2, 2, 20, None),
    ("Melhorar validações de input", "Usar marshmallow ou pydantic", "pending", 3, 0, 0, None, "improvement,validation"),
)


def _password_for(key):
    password = current_app.config.get(key)
    if password:
        return password
    password = secrets.token_urlsafe(GENERATED_PASSWORD_BYTES)
    # Exibida uma única vez para permitir o primeiro login em desenvolvimento.
    logger.warning("%s não definida; senha gerada para o seed: %s", key, password)
    return password


def _clear():
    Task.query.delete()
    User.query.delete()
    Category.query.delete()
    db.session.commit()


def run_seed(reset=False):
    if current_app.config["APP_ENV"] == "production":
        logger.warning("Seed ignorado em produção (APP_ENV=production).")
        return False

    if reset:
        _clear()
    elif User.query.first() is not None:
        logger.info("Banco já possui dados; seed ignorado (use --reset para recriar).")
        return False

    users = []
    for spec in USERS:
        user = User(name=spec["name"], email=spec["email"], role=spec["role"])
        user.set_password(_password_for(spec["password_key"]))
        users.append(user)
    categories = [Category(**spec) for spec in CATEGORIES]
    db.session.add_all(users + categories)
    db.session.flush()

    now = utc_now()
    for title, description, status, priority, user_idx, category_idx, due_in_days, tags in TASKS:
        db.session.add(Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            user_id=users[user_idx].id,
            category_id=categories[category_idx].id,
            due_date=now + timedelta(days=due_in_days) if due_in_days is not None else None,
            tags=tags,
        ))

    db.session.commit()
    logger.info(
        "Seed concluído: %s usuários, %s categorias, %s tasks",
        User.query.count(), Category.query.count(), Task.query.count(),
    )
    return True
