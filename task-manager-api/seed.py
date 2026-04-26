"""Seed script — populate database with sample data."""
from app import app, db
from models.user import User
from models.task import Task
from models.category import Category
from datetime import datetime, timezone, timedelta


def seed_data():
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = [
            User(name='João Silva', email='joao@email.com', role='admin'),
            User(name='Maria Santos', email='maria@email.com', role='user'),
            User(name='Pedro Oliveira', email='pedro@email.com', role='manager'),
        ]
        users[0].set_password('1234')
        users[1].set_password('abcd')
        users[2].set_password('pass')
        db.session.add_all(users)
        db.session.commit()

        categories = [
            Category(name='Backend', description='Tarefas de backend', color='#3498db'),
            Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71'),
            Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c'),
            Category(name='Bug', description='Correção de bugs', color='#e67e22'),
        ]
        db.session.add_all(categories)
        db.session.commit()

        now = datetime.now(timezone.utc)
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': users[0].id, 'category_id': categories[0].id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': users[1].id, 'category_id': categories[1].id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': users[2].id, 'category_id': categories[2].id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': users[0].id, 'category_id': categories[3].id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': users[0].id, 'category_id': categories[0].id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': users[1].id, 'category_id': categories[0].id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': users[2].id, 'category_id': categories[0].id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': users[1].id, 'category_id': categories[0].id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': users[2].id, 'category_id': categories[2].id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': users[0].id, 'category_id': categories[0].id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            task = Task(
                title=td['title'],
                description=td['description'],
                status=td['status'],
                priority=td['priority'],
                user_id=td['user_id'],
                category_id=td['category_id'],
            )
            if 'due_date' in td:
                task.due_date = td['due_date']
            if 'tags' in td:
                task.tags = td['tags']
            db.session.add(task)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == '__main__':
    seed_data()
