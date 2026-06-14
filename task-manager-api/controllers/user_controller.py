import re
from database import db
from models.user import User
from models.task import Task
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH


class UserController:

    @staticmethod
    def get_all():
        users = User.query.all()
        return [{**u.to_dict(), 'task_count': len(u.tasks)} for u in users], 200

    @staticmethod
    def get_by_id(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
        return data, 200

    @staticmethod
    def create(data):
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

        if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
            return {'error': 'Email inválido'}, 400

        if len(password) < MIN_PASSWORD_LENGTH:
            return {'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}, 400

        if User.query.filter_by(email=email).first():
            return {'error': 'Email já cadastrado'}, 409

        if role not in VALID_ROLES:
            return {'error': 'Role inválido'}, 400

        user = User(name=name, email=email, role=role)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user.to_dict(), 201
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def update(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', data['email']):
                return {'error': 'Email inválido'}, 400
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return {'error': 'Email já cadastrado'}, 409
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                return {'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}, 400
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                return {'error': 'Role inválido'}, 400
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        try:
            db.session.commit()
            return user.to_dict(), 200
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def delete(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        try:
            Task.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
            return {'message': 'Usuário deletado com sucesso'}, 200
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def get_tasks(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404
        result = []
        for t in Task.query.filter_by(user_id=user_id).all():
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            result.append(data)
        return result, 200

    @staticmethod
    def login(data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {'error': 'Email e senha são obrigatórios'}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {'error': 'Credenciais inválidas'}, 401

        if not user.active:
            return {'error': 'Usuário inativo'}, 403

        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id))
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': token,
        }, 200
