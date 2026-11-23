"""Script para popular o banco com dados iniciais"""
from datetime import timedelta

from src.app import create_app
from src.models import Category, Task, User, db, utcnow
from src.models.user_model import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER

USERS = [
    {"name": "João Silva", "email": "joao@email.com", "password": "1234", "role": ROLE_ADMIN},
    {"name": "Maria Santos", "email": "maria@email.com", "password": "abcd", "role": ROLE_USER},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "password": "pass", "role": ROLE_MANAGER},
]

CATEGORIES = [
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
]


def build_tasks(users, categories):
    joao, maria, pedro = users
    backend, frontend, devops, bug = categories
    now = utcnow()
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user': joao, 'category': backend, 'due_date': now - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user': maria, 'category': frontend, 'due_date': now + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user': pedro, 'category': devops, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user': joao, 'category': bug, 'due_date': now - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user': joao, 'category': backend, 'due_date': now + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user': maria, 'category': backend},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user': pedro, 'category': backend},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user': maria, 'category': backend, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user': pedro, 'category': devops, 'due_date': now + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user': joao, 'category': backend, 'tags': 'improvement,validation'},
    ]


def seed_data(app=None):
    app = app or create_app()
    with app.app_context():
        db.session.execute(db.delete(Task))
        db.session.execute(db.delete(User))
        db.session.execute(db.delete(Category))

        users = []
        for data in USERS:
            user = User(name=data["name"], email=data["email"], role=data["role"])
            user.set_password(data["password"])
            users.append(user)
        categories = [Category(**data) for data in CATEGORIES]
        db.session.add_all(users + categories)
        db.session.flush()

        for data in build_tasks(users, categories):
            db.session.add(Task(
                title=data['title'], description=data['description'], status=data['status'],
                priority=data['priority'], user_id=data['user'].id, category_id=data['category'].id,
                due_date=data.get('due_date'), tags=data.get('tags'),
            ))
        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {db.session.execute(db.select(db.func.count(User.id))).scalar_one()} usuários")
        print(f"  {db.session.execute(db.select(db.func.count(Category.id))).scalar_one()} categorias")
        print(f"  {db.session.execute(db.select(db.func.count(Task.id))).scalar_one()} tasks")


if __name__ == '__main__':
    seed_data()
