"""E-mail notification adapter. SMTP settings are injected by the composition root (read from env)."""
import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, smtp_settings, smtp_factory=smtplib.SMTP):
        self._smtp = smtp_settings
        self._smtp_factory = smtp_factory

    def send_email(self, to, subject, body):
        if not self._smtp.configured:
            logger.warning("SMTP not configured; e-mail to %s not sent", to)
            return False
        try:
            with self._smtp_factory(self._smtp.host, self._smtp.port) as server:
                server.starttls()
                server.login(self._smtp.user, self._smtp.password)
                server.sendmail(self._smtp.user, to, f"Subject: {subject}\n\n{body}")
        except (smtplib.SMTPException, OSError):
            logger.exception("Erro ao enviar email para %s", to)
            return False
        logger.info("Email enviado para %s", to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
