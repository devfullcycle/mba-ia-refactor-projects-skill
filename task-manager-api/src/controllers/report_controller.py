"""Controller de Relatórios.

O `summary_report` do legado tinha 90 linhas em um único handler, com 15 queries sequenciais
e uma query extra por usuário. Aqui a agregação é feita em SQL pelos models e o controller
apenas compõe a resposta.
"""
from datetime import timedelta

from src.domain.constants import PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_DONE
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import now_utc


def _percentual(parte, total):
    return round((parte / total) * 100, 2) if total > 0 else 0


class ReportController:
    def summary(self):
        agora = now_utc()
        por_status = Task.count_by_status()
        por_prioridade = Task.count_by_priority()
        atrasadas = Task.overdue_tasks()
        desde = agora - timedelta(days=RECENT_ACTIVITY_DAYS)

        return {
            "generated_at": str(agora),
            "overview": {
                "total_tasks": Task.count(),
                "total_users": User.count(),
                "total_categories": Category.count(),
            },
            "tasks_by_status": {
                "pending": por_status.get("pending", 0),
                "in_progress": por_status.get("in_progress", 0),
                "done": por_status.get("done", 0),
                "cancelled": por_status.get("cancelled", 0),
            },
            "tasks_by_priority": {
                rotulo: por_prioridade.get(prioridade, 0)
                for prioridade, rotulo in PRIORITY_LABELS.items()
            },
            "overdue": {
                "count": len(atrasadas),
                "tasks": [
                    {
                        "id": tarefa.id,
                        "title": tarefa.title,
                        "due_date": str(tarefa.due_date),
                        "days_overdue": (agora - tarefa.due_date).days,
                    }
                    for tarefa in atrasadas
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": Task.count_created_since(desde),
                "tasks_completed_last_7_days": Task.count_done_since(desde),
            },
            "user_productivity": [
                {**linha, "completion_rate": _percentual(
                    linha["completed_tasks"], linha["total_tasks"]
                )}
                for linha in Task.productivity_by_user()
            ],
        }, 200

    def by_user(self, user_id):
        usuario = User.get(user_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")

        estatisticas = Task.statistics_for_user(user_id)
        por_status = estatisticas["por_status"]
        total = estatisticas["total"]
        concluidas = por_status.get(STATUS_DONE, 0)

        return {
            "user": {
                "id": usuario.id,
                "name": usuario.name,
                "email": usuario.email,
            },
            "statistics": {
                "total_tasks": total,
                "done": concluidas,
                "pending": por_status.get("pending", 0),
                "in_progress": por_status.get("in_progress", 0),
                "cancelled": por_status.get("cancelled", 0),
                "overdue": estatisticas["atrasadas"],
                "high_priority": estatisticas["alta_prioridade"],
                "completion_rate": _percentual(concluidas, total),
            },
        }, 200


class HealthController:
    def __init__(self, versao):
        self._versao = versao

    def index(self):
        return {"message": "Task Manager API", "version": self._versao}, 200

    def health(self):
        return {"status": "ok", "timestamp": str(now_utc())}, 200
