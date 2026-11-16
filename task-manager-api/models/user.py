import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.clock import utc_now
from utils.constants import ADMIN_ROLE, DEFAULT_ROLE

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def uses_legacy_hash(self):
        return bool(_LEGACY_MD5.match(self.password or ''))

    def check_password(self, pwd):
        if self.uses_legacy_hash():
            # Hashes MD5 antigos (anteriores à refatoração): aceitos só para
            # migração; o login com sucesso regrava o hash no formato seguro.
            legacy = hashlib.md5(pwd.encode(), usedforsecurity=False).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == ADMIN_ROLE
