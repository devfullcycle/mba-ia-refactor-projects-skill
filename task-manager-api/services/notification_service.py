import smtplib
import logging
from config import Config

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def send_email(to, subject, body):
        if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
            logger.warning("SMTP not configured — skipping email")
            return False

        try:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(Config.SMTP_USER, to, message)
            server.quit()
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def notify_task_assigned(user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        NotificationService.send_email(user.email, subject, body)

    @staticmethod
    def notify_task_overdue(user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        NotificationService.send_email(user.email, subject, body)
