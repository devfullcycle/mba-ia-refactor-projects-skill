"""User entity and its repository."""
import hashlib
import hmac

from sqlalchemy import case, func, select
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db, utcnow
from .task_model import STATUS_DONE, Task

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)

_MODERN_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Public representation — never includes the password hash."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        # Legacy unsalted MD5 row: verify once, then upgrade the hash transparently.
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True
        return False

    def is_admin(self):
        return self.role == ROLE_ADMIN


class UserRepository:
    def __init__(self, session):
        self.session = session

    def get(self, user_id):
        return self.session.get(User, user_id)

    def get_by_email(self, email):
        return self.session.scalars(select(User).where(User.email == email)).first()

    def count(self):
        return self.session.scalar(select(func.count(User.id)))

    def list_with_task_counts(self):
        stmt = (
            select(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        return self.session.execute(stmt).all()

    def productivity(self):
        """(user, total_tasks, completed_tasks) per user in a single query."""
        completed = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
        stmt = (
            select(User, func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        return self.session.execute(stmt).all()

    def add(self, user):
        self.session.add(user)

    def delete(self, user):
        self.session.delete(user)

    def commit(self):
        self.session.commit()
