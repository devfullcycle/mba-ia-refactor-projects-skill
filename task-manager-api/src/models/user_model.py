import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from src.models.database import db, utcnow

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
PRIVILEGED_ROLES = (ROLE_ADMIN, ROLE_MANAGER)
MIN_PASSWORD_LENGTH = 4

PUBLIC_FIELDS = ("id", "name", "email", "role", "active")
_LEGACY_MD5_LENGTH = 32


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
        data = {field: getattr(self, field) for field in PUBLIC_FIELDS}
        data["created_at"] = str(self.created_at)
        return data

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify the password; legacy unsalted MD5 rows are accepted once and upgraded in place."""
        if self._is_legacy_hash():
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            if not hmac.compare_digest(self.password, legacy):
                return False
            self.set_password(raw_password)
            return True
        return check_password_hash(self.password, raw_password)

    def _is_legacy_hash(self):
        return len(self.password) == _LEGACY_MD5_LENGTH and ":" not in self.password

    def is_admin(self):
        return self.role == ROLE_ADMIN


class UserRepository:
    def __init__(self, database):
        self.db = database

    def get(self, user_id):
        return self.db.session.get(User, user_id)

    def get_by_email(self, email):
        return self.db.session.execute(self.db.select(User).where(User.email == email)).scalar_one_or_none()

    def list_all(self):
        return self.db.session.execute(self.db.select(User).order_by(User.id)).scalars().all()

    def count(self):
        return self.db.session.execute(self.db.select(self.db.func.count(User.id))).scalar_one()

    def add(self, user):
        self.db.session.add(user)

    def delete(self, user):
        self.db.session.delete(user)

    def commit(self):
        self.db.session.commit()
