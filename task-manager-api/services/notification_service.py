import logging
import smtplib
from email.message import EmailMessage

from config import settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


def _single_line(text):
    """Remove quebras de linha de valores que vão para cabeçalhos (evita header injection)."""
    return ' '.join(str(text).splitlines())


class NotificationService:
    """Envio de e-mails. Credenciais SMTP vêm da configuração (variáveis de ambiente).

    Ainda não é chamado por nenhuma rota; mantido como serviço pronto para uso.
    """

    def __init__(self, host=None, port=None, user=None, password=None):
        self.email_host = host or settings.SMTP_HOST
        self.email_port = port or settings.SMTP_PORT
        self.email_user = user or settings.SMTP_USER
        self.email_password = password or settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        message = EmailMessage()
        message['From'] = self.email_user
        message['To'] = _single_line(to)
        message['Subject'] = _single_line(subject)
        message.set_content(body)
        try:
            # O context manager fecha a conexão mesmo se login/envio falhar.
            with smtplib.SMTP(self.email_host, self.email_port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception('Erro ao enviar email para %s', to)
            return False
        logger.info('Email enviado para %s', to)
        return True

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
