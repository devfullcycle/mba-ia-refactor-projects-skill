from database import db
from services.clock import utc_now
import hashlib
import re
from werkzeug.security import check_password_hash, generate_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self._has_legacy_md5_password():
            valid = self.password == hashlib.md5(pwd.encode()).hexdigest()
            if valid:
                self.set_password(pwd)
            return valid
        return check_password_hash(self.password, pwd)

    def _has_legacy_md5_password(self):
        return bool(re.fullmatch(r"[0-9a-f]{32}", self.password or ""))

    def is_admin(self):
        return self.role == 'admin'
