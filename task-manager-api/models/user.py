import hashlib
import hmac
import re

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.clock import utcnow

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")

_LEGACY_MD5_LENGTH = 32


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # ---- serialização (nunca inclui a senha) ---------------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def to_summary(self):
        return {"id": self.id, "name": self.name, "email": self.email}

    # ---- senha ---------------------------------------------------------------
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def _is_legacy_md5(self):
        return bool(self.password) and len(self.password) == _LEGACY_MD5_LENGTH and ":" not in self.password

    def check_password(self, raw_password):
        """Valida a senha; hashes MD5 legados são migrados para hash forte no primeiro login válido."""
        if self._is_legacy_md5():
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            if hmac.compare_digest(self.password, legacy):
                self.set_password(raw_password)
                return True
            return False
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # ---- consultas -----------------------------------------------------------
    @staticmethod
    def get(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def by_email(email):
        return db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    @staticmethod
    def all():
        return db.session.execute(db.select(User).order_by(User.id)).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(db.select(func.count(User.id)))
