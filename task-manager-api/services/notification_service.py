import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Email notification service. SMTP settings come from the app config (env-driven)."""

    def __init__(self, app=None):
        self.notifications = []
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.email_host = app.config.get("SMTP_HOST", "smtp.gmail.com")
        self.email_port = app.config.get("SMTP_PORT", 587)
        self.email_user = app.config.get("SMTP_USER", "")
        self.email_password = app.config.get("SMTP_PASSWORD", "")

    def notify_task_assigned(self, user, task):
        logger.info(
            "Notificando %s (user %s): nova task '%s'", user.email, user.id, task.title
        )
        self.notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": datetime_now(),
            }
        )


def datetime_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
