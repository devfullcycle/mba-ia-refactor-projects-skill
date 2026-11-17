import logging
import re
from sqlalchemy.orm import joinedload
from database import db
from models.user import User
from models.task import Task

logger = logging.getLogger(__name__)

class UserController:

    @staticmethod
    def get_all_users():
        """Recupera usuários com tarefas pré-carregadas via joinedload para evitar N+1 queries."""
        users = User.query.options(joinedload(User.tasks)).all()
        result = []
        for u in users:
            user_data = u.to_dict()
            user_data['task_count'] = len(u.tasks)
            result.append(user_data)
        return result, 200

    @staticmethod
    def get_user_by_id(user_id: int):
        user = User.query.options(joinedload(User.tasks)).filter(User.id == user_id).first()
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in user.tasks]
        return data, 200

    @staticmethod
    def create_user(data: dict):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            return {'error': 'Nome é obrigatório'}, 400
        if not email:
            return {'error': 'Email é obrigatório'}, 400
        if not password:
            return {'error': 'Senha é obrigatória'}, 400

        if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', str(email)):
            return {'error': 'Email inválido'}, 400

        if len(str(password)) < 4:
            return {'error': 'Senha deve ter no mínimo 4 caracteres'}, 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return {'error': 'Email já cadastrado'}, 409

        if role not in ['user', 'admin', 'manager']:
            return {'error': 'Role inválido'}, 400

        user = User()
        user.name = str(name).strip()
        user.email = str(email).strip().lower()
        user.set_password(str(password))
        user.role = role

        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"Usuário criado com sucesso: ID {user.id} - '{user.name}'")
            return user.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar usuário: {str(e)}", exc_info=True)
            return {'error': 'Erro ao criar usuário'}, 500

    @staticmethod
    def update_user(user_id: int, data: dict):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        if not data:
            return {'error': 'Dados inválidos'}, 400

        if 'name' in data:
            name = str(data['name']).strip()
            if name:
                user.name = name

        if 'email' in data:
            email = str(data['email']).strip().lower()
            if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
                return {'error': 'Email inválido'}, 400

            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user_id:
                return {'error': 'Email já cadastrado'}, 409
            user.email = email

        if 'password' in data:
            pwd = str(data['password'])
            if len(pwd) < 4:
                return {'error': 'Senha muito curta'}, 400
            user.set_password(pwd)

        if 'role' in data:
            role = data['role']
            if role not in ['user', 'admin', 'manager']:
                return {'error': 'Role inválido'}, 400
            user.role = role

        if 'active' in data:
            user.active = bool(data['active'])

        try:
            db.session.commit()
            logger.info(f"Usuário atualizado com sucesso: ID {user.id}")
            return user.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar usuário {user_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao atualizar'}, 500

    @staticmethod
    def delete_user(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        try:
            # Deleção atômica via cascade configurado no SQLAlchemy
            db.session.delete(user)
            db.session.commit()
            logger.info(f"Usuário deletado com sucesso: ID {user_id}")
            return {'message': 'Usuário deletado com sucesso'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar usuário {user_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao deletar'}, 500

    @staticmethod
    def get_user_tasks(user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        result = []
        for t in tasks:
            task_data = {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue()
            }
            result.append(task_data)
        return result, 200

    @staticmethod
    def login(data: dict):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {'error': 'Email e senha são obrigatórios'}, 400

        user = User.query.filter_by(email=str(email).strip().lower()).first()
        if not user or not user.check_password(str(password)):
            return {'error': 'Credenciais inválidas'}, 401

        if not user.active:
            return {'error': 'Usuário inativo'}, 403

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': f'fake-jwt-token-{user.id}'
        }, 200
