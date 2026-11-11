"""Notificações por e-mail. Credenciais vêm do ambiente; desabilitado até SMTP_ENABLED=true."""
import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


def send_email(to, subject, body):
    config = current_app.config
    if not config["SMTP_ENABLED"]:
        logger.info("SMTP desabilitado; e-mail para %s não enviado (%s)", to, subject)
        return False

    message = EmailMessage()
    message["From"] = config["SMTP_USER"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
            server.send_message(message)
    except (smtplib.SMTPException, OSError):
        # Falha de e-mail não deve derrubar a operação de negócio que a disparou.
        logger.exception("Erro ao enviar e-mail para %s", to)
        return False

    logger.info("E-mail enviado para %s", to)
    return True


def notify_task_assigned(user, task):
    subject = f"Nova task atribuída: {task.title}"
    body = (
        f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
        f"Prioridade: {task.priority}\nStatus: {task.status}"
    )
    return send_email(user.email, subject, body)
