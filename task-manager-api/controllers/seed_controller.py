from __future__ import annotations

from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from services.clock import utc_now


class SeedController:
    def __init__(self, seed_repository, session, clock=utc_now):
        self.repository = seed_repository
        self.session = session
        self.clock = clock

    def seed(self, passwords, after_stage=None):
        required = {"admin", "user", "manager"}
        missing = sorted(role for role in required if not passwords.get(role))
        if missing:
            raise ValueError(
                "Credenciais de seed ausentes para: " + ", ".join(missing)
            )

        try:
            self.repository.reset()
            self._stage(after_stage, "reset")

            users = self.repository.add_users(
                [
                    self._user("João Silva", "joao@email.com", "admin", passwords),
                    self._user("Maria Santos", "maria@email.com", "user", passwords),
                    self._user(
                        "Pedro Oliveira", "pedro@email.com", "manager", passwords
                    ),
                ],
                flush=True,
            )
            self._stage(after_stage, "users")

            categories = self.repository.add_categories(
                [
                    Category(name="Backend", description="Tarefas de backend", color="#3498db"),
                    Category(name="Frontend", description="Tarefas de frontend", color="#2ecc71"),
                    Category(name="DevOps", description="Tarefas de infraestrutura", color="#e74c3c"),
                    Category(name="Bug", description="Correção de bugs", color="#e67e22"),
                ],
                flush=True,
            )
            self._stage(after_stage, "categories")

            self.repository.add_tasks(self._tasks(users, categories))
            self._stage(after_stage, "tasks")
            self.session.commit()
            return self.repository.counts()
        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _stage(callback, name):
        if callback is not None:
            callback(name)

    @staticmethod
    def _user(name, email, role, passwords):
        user = User(name=name, email=email, role=role)
        user.set_password(passwords[role])
        return user

    def _tasks(self, users, categories):
        now = self.clock()
        data = [
            ("Implementar autenticação JWT", "Adicionar autenticação real com JWT", "pending", 1, 0, 0, now - timedelta(days=3), None),
            ("Criar tela de login", "Tela de login responsiva", "in_progress", 2, 1, 1, now + timedelta(days=5), None),
            ("Configurar CI/CD", "Pipeline com GitHub Actions", "done", 2, 2, 2, None, "devops,ci,github"),
            ("Corrigir bug no filtro de busca", "Filtro não funciona com caracteres especiais", "pending", 1, 0, 3, now - timedelta(days=1), None),
            ("Adicionar paginação na API", "Endpoints retornam todos os registros", "pending", 3, 0, 0, now + timedelta(days=10), None),
            ("Escrever testes unitários", "Cobertura mínima de 80%", "pending", 2, 1, 0, None, None),
            ("Documentar API com Swagger", "Gerar documentação automática", "cancelled", 4, 2, 0, None, None),
            ("Refatorar models", "Melhorar organização dos models", "in_progress", 3, 1, 0, None, "refactor,tech-debt"),
            ("Configurar monitoramento", "Prometheus + Grafana", "pending", 4, 2, 2, now + timedelta(days=20), None),
            ("Melhorar validações de input", "Usar marshmallow ou pydantic", "pending", 3, 0, 0, None, "improvement,validation"),
        ]
        return [
            Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                user_id=users[user_index].id,
                category_id=categories[category_index].id,
                due_date=due_date,
                tags=tags,
            )
            for (
                title,
                description,
                status,
                priority,
                user_index,
                category_index,
                due_date,
                tags,
            ) in data
        ]
