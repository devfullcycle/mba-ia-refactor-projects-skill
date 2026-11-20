"""Script para popular o banco com dados iniciais"""
from datetime import timedelta

from sqlalchemy import delete, func, select

from src.app import create_app
from src.models import Category, Task, User, db, utcnow

USERS = [
    {"name": "João Silva", "email": "joao@email.com", "password": "1234", "role": "admin"},
    {"name": "Maria Santos", "email": "maria@email.com", "password": "abcd", "role": "user"},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "password": "pass", "role": "manager"},
]

CATEGORIES = [
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
]


def _tasks(users, categories, now):
    joao, maria, pedro = users
    backend, frontend, devops, bug = categories
    return [
        {"title": "Implementar autenticação JWT", "description": "Adicionar autenticação real com JWT", "status": "pending", "priority": 1, "user": joao, "category": backend, "due_date": now - timedelta(days=3)},
        {"title": "Criar tela de login", "description": "Tela de login responsiva", "status": "in_progress", "priority": 2, "user": maria, "category": frontend, "due_date": now + timedelta(days=5)},
        {"title": "Configurar CI/CD", "description": "Pipeline com GitHub Actions", "status": "done", "priority": 2, "user": pedro, "category": devops, "tags": "devops,ci,github"},
        {"title": "Corrigir bug no filtro de busca", "description": "Filtro não funciona com caracteres especiais", "status": "pending", "priority": 1, "user": joao, "category": bug, "due_date": now - timedelta(days=1)},
        {"title": "Adicionar paginação na API", "description": "Endpoints retornam todos os registros", "status": "pending", "priority": 3, "user": joao, "category": backend, "due_date": now + timedelta(days=10)},
        {"title": "Escrever testes unitários", "description": "Cobertura mínima de 80%", "status": "pending", "priority": 2, "user": maria, "category": backend},
        {"title": "Documentar API com Swagger", "description": "Gerar documentação automática", "status": "cancelled", "priority": 4, "user": pedro, "category": backend},
        {"title": "Refatorar models", "description": "Melhorar organização dos models", "status": "in_progress", "priority": 3, "user": maria, "category": backend, "tags": "refactor,tech-debt"},
        {"title": "Configurar monitoramento", "description": "Prometheus + Grafana", "status": "pending", "priority": 4, "user": pedro, "category": devops, "due_date": now + timedelta(days=20)},
        {"title": "Melhorar validações de input", "description": "Usar marshmallow ou pydantic", "status": "pending", "priority": 3, "user": joao, "category": backend, "tags": "improvement,validation"},
    ]


def seed_data(app):
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(delete(model))
        db.session.commit()

        users = []
        for data in USERS:
            user = User(name=data["name"], email=data["email"], role=data["role"])
            user.set_password(data["password"])
            users.append(user)
        categories = [Category(**data) for data in CATEGORIES]
        db.session.add_all(users + categories)
        db.session.commit()

        for data in _tasks(users, categories, utcnow()):
            user, category = data.pop("user"), data.pop("category")
            db.session.add(Task(user_id=user.id, category_id=category.id, **data))
        db.session.commit()

        # CLI script output (not request-path logging)
        print("Seed concluído com sucesso!")
        for label, model in (("usuários", User), ("categorias", Category), ("tasks", Task)):
            print(f"  {db.session.scalar(select(func.count(model.id)))} {label}")


if __name__ == "__main__":
    seed_data(create_app())
