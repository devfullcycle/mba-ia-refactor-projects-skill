"""User entity and repository."""
import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from src.models.constants import ROLE_ADMIN, ROLE_USER
from src.models.database import BaseRepository, db, utcnow

_MODERN_HASH_PREFIXES = ("scrypt:", "pbkdf2:")
PUBLIC_FIELDS = ("id", "name", "email", "role", "active")


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
        data = {field: getattr(self, field) for field in PUBLIC_FIELDS}
        data["created_at"] = str(self.created_at)
        return data

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def verify_password(self, raw_password):
        """Returns (valid, upgraded). Legacy MD5 hashes are verified once and re-hashed."""
        if self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password), False
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()  # legacy rows only
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True, True
        return False, False

    def is_admin(self):
        return self.role == ROLE_ADMIN


class UserRepository(BaseRepository):
    model = User

    def get_by_email(self, email):
        return self.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    def list_all(self):
        return self.session.execute(db.select(User).order_by(User.id)).scalars().all()

    def count(self):
        return self.session.execute(db.select(db.func.count(User.id))).scalar_one()
