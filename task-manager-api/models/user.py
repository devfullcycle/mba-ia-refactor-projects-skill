from database import db
from datetime import datetime, timezone
import bcrypt


def _now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pwd):
        return bcrypt.checkpw(pwd.encode(), self.password.encode())

    def is_admin(self):
        return self.role == "admin"
