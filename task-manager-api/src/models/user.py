import hashlib
import hmac
import re

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from src.config.database import db
from src.utils.dates import format_datetime, utc_now

ROLE_USER = "user"
ROLE_MANAGER = "manager"
ROLE_ADMIN = "admin"
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
# Perfis que gerenciam tasks e categorias de qualquer usuário.
STAFF_ROLES = (ROLE_ADMIN, ROLE_MANAGER)

NAME_MAX_LENGTH = 100
EMAIL_MAX_LENGTH = 150
PASSWORD_MIN_LENGTH = 8

# Hashes gravados pelo sistema legado: MD5 hexadecimal sem salt.
_LEGACY_MD5_REGEX = re.compile(r"^[0-9a-f]{32}$")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_MAX_LENGTH), nullable=False)
    email = db.Column(db.String(EMAIL_MAX_LENGTH), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # O hash da senha nunca sai na serialização pública.
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": format_datetime(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def has_legacy_password(self):
        return bool(self.password and _LEGACY_MD5_REGEX.match(self.password))

    def check_password(self, raw_password):
        if self.has_legacy_password():
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_staff(self):
        return self.role in STAFF_ROLES


def find_by_id(user_id):
    return db.session.get(User, user_id)


def find_by_email(email):
    return User.query.filter(func.lower(User.email) == email.lower()).first()


def list_with_task_count():
    """Usuários + total de tasks em uma única query (antes: len(u.tasks) por usuário)."""
    from src.models.task import Task

    return (
        db.session.query(User, func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )


def count():
    return db.session.query(func.count(User.id)).scalar()


def create(name, email, password, role=ROLE_USER):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def save():
    db.session.commit()


def delete(user):
    # cascade="all, delete-orphan" em Task.user remove as tasks do usuário na mesma transação.
    db.session.delete(user)
    db.session.commit()
