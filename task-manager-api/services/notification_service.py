import smtplib
from services.clock import utc_now


class NotificationDeliveryError(RuntimeError):
    pass


class NotificationService:
    def __init__(self, host, port, user, password, timeout_seconds=10):
        self.notifications = []
        self.email_host = host
        self.email_port = port
        self.email_user = user
        self.email_password = password
        self.timeout_seconds = timeout_seconds

    def send_email(self, to, subject, body):
        if not all((self.email_host, self.email_user, self.email_password)):
            raise RuntimeError("Configuração SMTP incompleta")
        try:
            with smtplib.SMTP(
                self.email_host,
                self.email_port,
                timeout=self.timeout_seconds,
            ) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(self.email_user, to, message)
            return True
        except (OSError, smtplib.SMTPException) as error:
            raise NotificationDeliveryError("Falha ao enviar notificação") from error

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now()
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        result = []
        for n in self.notifications:
            if n['user_id'] == user_id:
                result.append(n)
        return result
