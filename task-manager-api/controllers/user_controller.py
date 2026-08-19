from flask import request, jsonify
from database import db
from models.user import User
from models.task import Task
from datetime import datetime, timezone
import re

def get_users():
    try:
        users = User.query.all()
        result = []
        for u in users:
            result.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': len(u.tasks)
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        data = user.to_dict()
        tasks = Task.query.filter_by(user_id=user_id).all()
        data['tasks'] = [t.to_dict() for t in tasks]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not email:
            return jsonify({'error': 'Email é obrigatório'}), 400
        if not password:
            return jsonify({'error': 'Senha é obrigatória'}), 400

        if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
            return jsonify({'error': 'Email inválido'}), 400

        if len(password) < 4:
            return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'}), 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({'error': 'Email já cadastrado'}), 409

        if role not in ['user', 'admin', 'manager']:
            return jsonify({'error': 'Role inválido'}), 400

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar usuário: {str(e)}'}), 500

def update_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', data['email']):
                return jsonify({'error': 'Email inválido'}), 400

            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email já cadastrado'}), 409
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < 4:
                return jsonify({'error': 'Senha muito curta'}), 400
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in ['user', 'admin', 'manager']:
                return jsonify({'error': 'Role inválido'}), 400
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500

def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        for t in tasks:
            db.session.delete(t)

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar: {str(e)}'}), 500

def get_user_tasks(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        return jsonify([t.to_dict() for t in tasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciais inválidas'}), 401

        if not user.active:
            return jsonify({'error': 'Usuário inativo'}), 403

        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
