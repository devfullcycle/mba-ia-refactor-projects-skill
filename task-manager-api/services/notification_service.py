"""Serviço de notificações por e-mail.

Credenciais lidas de config/ambiente; nenhum segredo hardcoded.
Em produção, o envio é assíncrono/fila; aqui mantemos um registro em memória
limitado (sem estado global ilimitado).
"""

import logging
import smtplib
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._notifications = []
        self.email_host = settings.SMTP_HOST
        self.email_port = settings.SMTP_PORT
        self.email_user = settings.SMTP_USER
        self.email_password = settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        # Se não configurado SMTP, apenas registra (não tenta enviar com cred fake).
        if not self.email_user or not self.email_password:
            logger.warning("SMTP não configurado; notificação para %s não enviada", to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception as exc:
            logger.error("Erro ao enviar email: %s", exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        # Mantém histórico limitado (não acumula infinitamente).
        self._notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": datetime.utcnow(),
            }
        )
        if len(self._notifications) > 500:
            self._notifications = self._notifications[-100:]

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self._notifications if n["user_id"] == user_id]


notification_service = NotificationService()