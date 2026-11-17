import logging
import smtplib
from datetime import datetime, timezone
from config.settings import Config

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.notifications = []
        self.email_host = host or Config.SMTP_HOST
        self.email_port = port or Config.SMTP_PORT
        self.email_user = user or Config.SMTP_USER
        self.email_password = password or Config.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.warning("Credenciais SMTP não configuradas. Simulação de envio de e-mail.")
            return True

        try:
            server = smtplib.SMTP(self.email_host, self.email_port, timeout=10)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info(f"Email enviado com sucesso para {to}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email para {to}: {str(e)}", exc_info=True)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': datetime.now(timezone.utc)
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n.get('user_id') == user_id]
