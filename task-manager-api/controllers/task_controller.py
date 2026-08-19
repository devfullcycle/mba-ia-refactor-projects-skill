from flask import request, jsonify
from services.task_service import TaskService

def get_tasks():
    try:
        tasks = TaskService.get_tasks(request.args)
        return jsonify([t.to_dict() for t in tasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_task(task_id):
    try:
        task = TaskService.get_task(task_id)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        return jsonify(task.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        task = TaskService.create_task(data)
        return jsonify(task.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_task(task_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        task = TaskService.update_task(task_id, data)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        return jsonify(task.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def delete_task(task_id):
    try:
        if TaskService.delete_task(task_id):
            return jsonify({'message': 'Tarefa deletada com sucesso'}), 200
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
