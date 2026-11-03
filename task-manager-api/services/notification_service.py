"""Serviço de notificações por e-mail. Credenciais vêm da config; sem SMTP configurado, apenas registra em log."""
import logging
import smtplib
from email.message import EmailMessage

from utils.clock import utcnow


class NotificationService:
    def __init__(self, settings, logger=None):
        self._settings = settings
        self._logger = logger or logging.getLogger(__name__)
        self._notifications = []

    def send_email(self, to, subject, body):
        if not self._settings.EMAIL_ENABLED or not self._settings.SMTP_USER:
            self._logger.info("E-mail (simulado) para %s: %s", to, subject)
            return False
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self._settings.SMTP_USER, to, subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self._settings.SMTP_HOST, self._settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(self._settings.SMTP_USER, self._settings.SMTP_PASSWORD)
                server.send_message(message)
            self._logger.info("E-mail enviado para %s", to)
            return True
        except (smtplib.SMTPException, OSError):
            self._logger.exception("Erro ao enviar e-mail para %s", to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        self.send_email(user.email, subject, body)
        self._notifications.append({
            "type": "task_assigned", "user_id": user.id, "task_id": task.id, "timestamp": utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self._notifications if n["user_id"] == user_id]
