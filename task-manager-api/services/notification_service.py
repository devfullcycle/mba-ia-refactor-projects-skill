import logging
import smtplib

from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Envio de e-mails. Credenciais SMTP vêm da configuração (variáveis de ambiente)."""

    def __init__(self, host=None, port=None, user=None, password=None):
        self.email_host = host or settings.SMTP_HOST
        self.email_port = port or settings.SMTP_PORT
        self.email_user = user or settings.SMTP_USER
        self.email_password = password or settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info('Email enviado para %s', to)
            return True
        except Exception:
            logger.exception('Erro ao enviar email para %s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você."
            f"\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!"
            f"\n\nData limite: {task.due_date}"
        )
        return self.send_email(user.email, subject, body)
