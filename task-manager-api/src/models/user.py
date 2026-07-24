"""Model de Usuário — entidade, invariantes e acesso a dados do agregado.

Duas correções em relação ao legado: o hash passa a ser scrypt com salt (era MD5 sem salt) e
`to_dict()` não expõe mais o hash.
"""
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.constants import ROLE_ADMIN, ROLE_USER
from src.extensions import db
from src.utils.datetime_utils import now_utc


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # Dimensionada para o formato do werkzeug (scrypt), bem maior que o digest MD5.
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc)

    # --- serialização ---

    def to_dict(self):
        """Forma pública da entidade. O hash de senha nunca sai daqui."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    # --- invariantes / regras do agregado ---

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # --- acesso a dados ---

    @staticmethod
    def get(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def find_by_email(email):
        return db.session.scalars(select(User).where(User.email == email)).first()

    @staticmethod
    def email_taken(email, exclude_id=None):
        statement = select(User.id).where(User.email == email)
        if exclude_id is not None:
            statement = statement.where(User.id != exclude_id)
        return db.session.scalars(statement).first() is not None

    @staticmethod
    def list_with_task_counts():
        """Usuários com a contagem de tarefas em uma única query (o legado usava
        `len(u.tasks)`, que disparava um SELECT por usuário)."""
        from src.models.task import Task

        rows = db.session.execute(
            select(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()
        return [(user, total) for user, total in rows]

    @staticmethod
    def count():
        return db.session.scalar(select(func.count(User.id))) or 0

    @staticmethod
    def list_all():
        return list(db.session.scalars(select(User).order_by(User.id)))
