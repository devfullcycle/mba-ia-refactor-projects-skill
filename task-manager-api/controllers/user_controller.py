from database import db
from models.user import User
from models.task import Task
from utils.helpers import validate_email, VALID_ROLES, MIN_PASSWORD_LENGTH


class UserController:

    @staticmethod
    def get_all():
        users = User.query.all()
        return [
            {
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': len(u.tasks),
            }
            for u in users
        ], 200

    @staticmethod
    def get_by_id(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
        return data, 200

    @staticmethod
    def create(data):
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

        if not validate_email(email):
            return {'error': 'Email inválido'}, 400

        if len(password) < MIN_PASSWORD_LENGTH:
            return {'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}, 400

        if User.query.filter_by(email=email).first():
            return {'error': 'Email já cadastrado'}, 409

        if role not in VALID_ROLES:
            return {'error': 'Role inválido'}, 400

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        db.session.add(user)
        db.session.commit()
        return user.to_dict(), 201

    @staticmethod
    def update(user_id, data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not validate_email(data['email']):
                return {'error': 'Email inválido'}, 400
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return {'error': 'Email já cadastrado'}, 409
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                return {'error': 'Senha muito curta'}, 400
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                return {'error': 'Role inválido'}, 400
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict(), 200

    @staticmethod
    def delete(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        Task.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        return {'message': 'Usuário deletado com sucesso'}, 200

    @staticmethod
    def get_tasks(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        return [
            {
                **task.to_dict(),
                'overdue': task.is_overdue(),
            }
            for task in tasks
        ], 200

    @staticmethod
    def login(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {'error': 'Email e senha são obrigatórios'}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {'error': 'Credenciais inválidas'}, 401

        if not user.active:
            return {'error': 'Usuário inativo'}, 403

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id),
        }, 200
