"""Popula o banco com dados iniciais.

Senhas: SEED_PASSWORD (do ambiente) para todos os usuários; sem ela, cada usuário
recebe uma senha aleatória, impressa ao final. Nenhuma senha fixa fica no código.
"""
import secrets
from datetime import timedelta

from sqlalchemy import delete, func, select

from app import create_app
from config import settings
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'role': 'manager'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]


def _tasks(joao, maria, pedro, backend, frontend, devops, bug):
    now = utc_now()
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': now + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': now - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': now + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
    ]


def seed_data():
    app = create_app()
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(delete(model))
        db.session.commit()

        credentials = []
        users = []
        for data in USERS:
            password = settings.SEED_PASSWORD or secrets.token_urlsafe(9)
            user = User(**data)
            user.set_password(password)
            users.append(user)
            credentials.append((data['email'], data['role'], password))
        categories = [Category(**data) for data in CATEGORIES]
        db.session.add_all(users + categories)
        db.session.commit()

        db.session.add_all(Task(**data) for data in _tasks(*users, *categories))
        db.session.commit()

        print("Seed concluído com sucesso!")
        for label, model in (('usuários', User), ('categorias', Category), ('tasks', Task)):
            count = db.session.scalar(select(func.count()).select_from(model))
            print(f"  {count} {label}")
        print("Credenciais (use em POST /login):")
        for email, role, password in credentials:
            print(f"  {email} ({role}): {password}")


if __name__ == '__main__':
    seed_data()
