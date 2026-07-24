"""Popula o banco com dados iniciais de demonstração.

Uso: python seed.py

As senhas abaixo são credenciais de demonstração e ficam abaixo do mínimo exigido pela API
(`PASSWORD_MIN_LENGTH`), que só se aplica ao cadastro via endpoint. Em um ambiente real, a
migração exigiria redefinição de senha.
"""
from datetime import timedelta

from src.app import create_app
from src.extensions import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import now_utc

USUARIOS = [
    {"name": "João Silva", "email": "joao@email.com", "password": "1234", "role": "admin"},
    {"name": "Maria Santos", "email": "maria@email.com", "password": "abcd", "role": "user"},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "password": "pass", "role": "manager"},
]

CATEGORIAS = [
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
]


def _tasks(agora, usuarios, categorias):
    joao, maria, pedro = usuarios
    backend, frontend, devops, bug = categorias
    return [
        {
            "title": "Implementar autenticação JWT",
            "description": "Adicionar autenticação real com JWT",
            "status": "pending",
            "priority": 1,
            "user_id": joao.id,
            "category_id": backend.id,
            "due_date": agora - timedelta(days=3),
        },
        {
            "title": "Criar tela de login",
            "description": "Tela de login responsiva",
            "status": "in_progress",
            "priority": 2,
            "user_id": maria.id,
            "category_id": frontend.id,
            "due_date": agora + timedelta(days=5),
        },
        {
            "title": "Configurar CI/CD",
            "description": "Pipeline com GitHub Actions",
            "status": "done",
            "priority": 2,
            "user_id": pedro.id,
            "category_id": devops.id,
            "tags": "devops,ci,github",
        },
        {
            "title": "Corrigir bug no filtro de busca",
            "description": "Filtro não funciona com caracteres especiais",
            "status": "pending",
            "priority": 1,
            "user_id": joao.id,
            "category_id": bug.id,
            "due_date": agora - timedelta(days=1),
        },
        {
            "title": "Adicionar paginação na API",
            "description": "Endpoints retornam todos os registros",
            "status": "pending",
            "priority": 3,
            "user_id": joao.id,
            "category_id": backend.id,
            "due_date": agora + timedelta(days=10),
        },
        {
            "title": "Escrever testes unitários",
            "description": "Cobertura mínima de 80%",
            "status": "pending",
            "priority": 2,
            "user_id": maria.id,
            "category_id": backend.id,
        },
        {
            "title": "Documentar API com Swagger",
            "description": "Gerar documentação automática",
            "status": "cancelled",
            "priority": 4,
            "user_id": pedro.id,
            "category_id": backend.id,
        },
        {
            "title": "Refatorar models",
            "description": "Melhorar organização dos models",
            "status": "in_progress",
            "priority": 3,
            "user_id": maria.id,
            "category_id": backend.id,
            "tags": "refactor,tech-debt",
        },
        {
            "title": "Configurar monitoramento",
            "description": "Prometheus + Grafana",
            "status": "pending",
            "priority": 4,
            "user_id": pedro.id,
            "category_id": devops.id,
            "due_date": agora + timedelta(days=20),
        },
        {
            "title": "Melhorar validações de input",
            "description": "Usar marshmallow ou pydantic",
            "status": "pending",
            "priority": 3,
            "user_id": joao.id,
            "category_id": backend.id,
            "tags": "improvement,validation",
        },
    ]


def seed_data():
    app = create_app()
    with app.app_context():
        db.session.query(Task).delete()
        db.session.query(User).delete()
        db.session.query(Category).delete()
        db.session.commit()

        usuarios = []
        for dados in USUARIOS:
            usuario = User(
                name=dados["name"], email=dados["email"], role=dados["role"]
            )
            usuario.set_password(dados["password"])
            db.session.add(usuario)
            usuarios.append(usuario)

        categorias = [Category(**dados) for dados in CATEGORIAS]
        db.session.add_all(categorias)
        db.session.commit()

        agora = now_utc()
        for dados in _tasks(agora, usuarios, categorias):
            tarefa = Task()
            for campo, valor in dados.items():
                if campo == "tags":
                    tarefa.set_tags(valor.split(","))
                else:
                    setattr(tarefa, campo, valor)
            db.session.add(tarefa)

        db.session.commit()

        app.logger.info(
            "Seed concluído: %s usuários, %s categorias, %s tasks",
            User.count(),
            Category.count(),
            Task.count(),
        )
        print("Seed concluído com sucesso!")
        print(f"  {User.count()} usuários")
        print(f"  {Category.count()} categorias")
        print(f"  {Task.count()} tasks")


if __name__ == "__main__":
    seed_data()
