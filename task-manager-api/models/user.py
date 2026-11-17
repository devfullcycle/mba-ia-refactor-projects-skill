from database import db
from datetime import datetime, timezone
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = db.relationship('Task', backref='user', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        """Retorna representação serializada sem expor credenciais de senha."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd: str) -> None:
        """Gera hash seguro com salt utilizando algoritmo PBKDF2/scrypt via Werkzeug."""
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        """Verifica a senha contra o hash seguro com retrocompatibilidade para MD5 legado."""
        if not self.password or not pwd:
            return False
        # Suporte a hashes werkzeug (scrypt, pbkdf2)
        if self.password.startswith('scrypt:') or self.password.startswith('pbkdf2:'):
            return check_password_hash(self.password, pwd)
        # Compatibilidade com hashes MD5 legados do banco inicial
        if len(self.password) == 32 and hashlib.md5(pwd.encode()).hexdigest() == self.password:
            # Upgrade transparente para hash seguro ao validar
            self.set_password(pwd)
            db.session.commit()
            return True
        return False

    def is_admin(self) -> bool:
        return self.role == 'admin'
