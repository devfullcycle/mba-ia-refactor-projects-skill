"""Serviço de notificação.

No legado esta classe existia com 48 linhas, credenciais de SMTP hardcoded — e **nunca era
instanciada**. Aqui ela passa a ser usada de fato (atribuição de tarefa), com transporte
configurável: sem SMTP configurado, a notificação é registrada no log em vez de falhar.
"""
import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class LogTransport:
    """Transporte de desenvolvimento: registra a notificação em vez de enviar e-mail."""

    def send(self, destinatario, assunto, corpo):
        logger.info(
            "Notificação registrada", extra={"destinatario": destinatario, "assunto": assunto}
        )
        logger.debug("Corpo da notificação para %s: %s", destinatario, corpo)
        return True


class SmtpTransport:
    """Transporte real. Credenciais vêm da configuração, nunca do código."""

    def __init__(self, host, port, user, password, timeout=10):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._timeout = timeout

    def send(self, destinatario, assunto, corpo):
        mensagem = EmailMessage()
        mensagem["Subject"] = assunto
        mensagem["From"] = self._user
        mensagem["To"] = destinatario
        mensagem.set_content(corpo)
        try:
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as servidor:
                servidor.starttls()
                servidor.login(self._user, self._password)
                servidor.send_message(mensagem)
            logger.info("E-mail enviado", extra={"destinatario": destinatario})
            return True
        except (smtplib.SMTPException, OSError) as erro:
            # Falha de notificação não pode derrubar a operação de negócio.
            logger.error("Falha ao enviar e-mail: %s", erro)
            return False


class NotificationService:
    def __init__(self, transport=None):
        self._transport = transport or LogTransport()

    def task_assigned(self, user, task):
        if user is None:
            return False
        assunto = f"Nova task atribuída: {task.title}"
        corpo = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self._transport.send(user.email, assunto, corpo)

    def task_overdue(self, user, task):
        if user is None:
            return False
        assunto = f"Task atrasada: {task.title}"
        corpo = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        )
        return self._transport.send(user.email, assunto, corpo)


def build_notification_service(config_smtp):
    """Escolhe o transporte conforme a configuração disponível."""
    host = config_smtp.get("host")
    user = config_smtp.get("user")
    password = config_smtp.get("password")
    if host and user and password:
        return NotificationService(
            SmtpTransport(host, int(config_smtp.get("port") or 587), user, password)
        )
    logger.info("SMTP não configurado — notificações serão registradas no log")
    return NotificationService(LogTransport())
