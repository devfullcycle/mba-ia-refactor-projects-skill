"""E-mail notification adapter. Configuration is injected by the composition root."""
import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @property
    def enabled(self):
        return bool(self.host and self.user)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info("SMTP não configurado; e-mail para %s não enviado", to)
            return False
        message = f"Subject: {subject}\n\n{body}"
        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, to, message)
        except (smtplib.SMTPException, OSError):
            logger.exception("Erro ao enviar e-mail para %s", to)
            return False
        logger.info("E-mail enviado para %s", to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
