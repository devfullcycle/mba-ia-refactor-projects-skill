import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ROLE_ADMIN, ROLE_USER
from database import db
from models.base import CrudMixin
from utils.helpers import utc_now

_LEGACY_MD5_RE = re.compile(r'^[0-9a-f]{32}$')


class User(CrudMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        """Representação pública: nunca inclui senha/hash."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # ------------------------------------------------------------------ senha
    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def uses_legacy_hash(self):
        """True se a senha ainda está no formato antigo (MD5 sem sal)."""
        return bool(_LEGACY_MD5_RE.match(self.password or ''))

    def check_password(self, pwd):
        if self.uses_legacy_hash():
            # Somente para migração: contas antigas são verificadas e re-hasheadas no login.
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # ---------------------------------------------------------- acesso a dados
    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
