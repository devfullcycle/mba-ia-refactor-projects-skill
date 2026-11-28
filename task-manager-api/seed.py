"""Script para popular o banco com dados iniciais."""
from datetime import timedelta

from src.app import create_app
from src.models import Category, Task, User
from src.models.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER
from src.models.database import db, utcnow


def _user(name, email, password, role):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    return user


def _category(name, description, color):
    category = Category(name=name, description=description, color=color)
    db.session.add(category)
    return category


def seed_data(app=None):
    app = app or create_app()
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(db.delete(model))
        db.session.commit()

        joao = _user('João Silva', 'joao@email.com', '1234', ROLE_ADMIN)
        maria = _user('Maria Santos', 'maria@email.com', 'abcd', ROLE_USER)
        pedro = _user('Pedro Oliveira', 'pedro@email.com', 'pass', ROLE_MANAGER)
        db.session.commit()

        backend = _category('Backend', 'Tarefas de backend', '#3498db')
        frontend = _category('Frontend', 'Tarefas de frontend', '#2ecc71')
        devops = _category('DevOps', 'Tarefas de infraestrutura', '#e74c3c')
        bug = _category('Bug', 'Correção de bugs', '#e67e22')
        db.session.commit()

        now = utcnow()
        tasks_data = [
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
        for task_data in tasks_data:
            db.session.add(Task(**task_data))
        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {db.session.execute(db.select(db.func.count(User.id))).scalar_one()} usuários")
        print(f"  {db.session.execute(db.select(db.func.count(Category.id))).scalar_one()} categorias")
        print(f"  {db.session.execute(db.select(db.func.count(Task.id))).scalar_one()} tasks")


if __name__ == '__main__':
    seed_data()
