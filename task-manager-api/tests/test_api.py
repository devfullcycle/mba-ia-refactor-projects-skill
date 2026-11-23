"""Script de validação automatizada de integridade dos endpoints da API refatorada."""
import sys
import os
import unittest
from datetime import datetime

from pathlib import Path
base_dir = str(Path(__file__).resolve().parent.parent)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from app import app, db
from seed import seed_data

class TestTaskManagerAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        with app.app_context():
            seed_data()

    def test_01_root_and_health(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Task Manager API', res.get_json()['message'])

        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['status'], 'ok')

    def test_02_get_tasks_with_joined_names(self):
        res = self.client.get('/tasks')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first_task = data[0]
        self.assertIn('title', first_task)
        self.assertIn('user_name', first_task)
        self.assertIn('category_name', first_task)
        self.assertIn('overdue', first_task)

    def test_03_get_task_by_id(self):
        res = self.client.get('/tasks/1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['id'], 1)
        self.assertIn('overdue', data)

        res_404 = self.client.get('/tasks/99999')
        self.assertEqual(res_404.status_code, 404)

    def test_04_create_and_update_task(self):
        new_task = {
            'title': 'Nova tarefa de teste',
            'description': 'Descrição teste unitário',
            'status': 'pending',
            'priority': 2,
            'user_id': 1,
            'category_id': 1,
            'due_date': '2026-12-31',
            'tags': ['refactor', 'test']
        }
        res = self.client.post('/tasks', json=new_task)
        self.assertEqual(res.status_code, 201)
        created = res.get_json()
        self.assertEqual(created['title'], 'Nova tarefa de teste')
        task_id = created['id']

        # Update
        res_put = self.client.put(f'/tasks/{task_id}', json={'status': 'done', 'priority': 1})
        self.assertEqual(res_put.status_code, 200)
        updated = res_put.get_json()
        self.assertEqual(updated['status'], 'done')
        self.assertEqual(updated['priority'], 1)

        # Delete
        res_del = self.client.delete(f'/tasks/{task_id}')
        self.assertEqual(res_del.status_code, 200)

    def test_05_task_search_and_stats(self):
        res = self.client.get('/tasks/search?q=autenticacao')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

        res_stats = self.client.get('/tasks/stats')
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()
        self.assertIn('total', stats)
        self.assertIn('completion_rate', stats)

    def test_06_users_and_security(self):
        res = self.client.get('/users')
        self.assertEqual(res.status_code, 200)
        users = res.get_json()
        self.assertGreater(len(users), 0)

        # Verificar se a senha está estritamente ausente do payload público
        for u in users:
            self.assertNotIn('password', u, "Vulnerabilidade: senha exposta no DTO de usuário!")
            self.assertIn('task_count', u)

    def test_07_user_detail_and_tasks(self):
        res = self.client.get('/users/1')
        self.assertEqual(res.status_code, 200)
        user = res.get_json()
        self.assertNotIn('password', user)
        self.assertIn('tasks', user)

        res_tasks = self.client.get('/users/1/tasks')
        self.assertEqual(res_tasks.status_code, 200)
        self.assertIsInstance(res_tasks.get_json(), list)

    def test_08_login_and_password_hashing(self):
        # Login com usuário pré-cadastrado no seed
        res = self.client.post('/login', json={'email': 'joao@email.com', 'password': '1234'})
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertIn('token', body)
        self.assertNotIn('password', body['user'])

        # Login inválido
        res_bad = self.client.post('/login', json={'email': 'joao@email.com', 'password': 'wrong'})
        self.assertEqual(res_bad.status_code, 401)

    def test_09_categories_crud(self):
        res = self.client.get('/categories')
        self.assertEqual(res.status_code, 200)
        cats = res.get_json()
        self.assertGreater(len(cats), 0)
        self.assertIn('task_count', cats[0])

        # Create
        res_post = self.client.post('/categories', json={'name': 'QA & Testes', 'color': '#1abc9c'})
        self.assertEqual(res_post.status_code, 201)
        cat_id = res_post.get_json()['id']

        # Update
        res_put = self.client.put(f'/categories/{cat_id}', json={'name': 'QA Automatizado'})
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.get_json()['name'], 'QA Automatizado')

        # Associate a task to verify prior disassociation on delete
        res_task = self.client.post('/tasks', json={
            'title': 'Tarefa com categoria temporária',
            'category_id': cat_id,
            'user_id': 1
        })
        self.assertEqual(res_task.status_code, 201)
        temp_task_id = res_task.get_json()['id']

        # Delete category
        res_del = self.client.delete(f'/categories/{cat_id}')
        self.assertEqual(res_del.status_code, 200)

        # Confirm category is gone
        res_cat_check = self.client.get('/categories')
        cat_ids = [c['id'] for c in res_cat_check.get_json()]
        self.assertNotIn(cat_id, cat_ids)

        # Confirm task is NOT deleted and its category_id was safely disassociated (set to None)
        res_task_check = self.client.get(f'/tasks/{temp_task_id}')
        self.assertEqual(res_task_check.status_code, 200)
        self.assertIsNone(res_task_check.get_json()['category_id'])

    def test_10_reports(self):
        res = self.client.get('/reports/summary')
        self.assertEqual(res.status_code, 200)
        rep = res.get_json()
        self.assertIn('overview', rep)
        self.assertIn('tasks_by_status', rep)
        self.assertIn('user_productivity', rep)

        res_user = self.client.get('/reports/user/1')
        self.assertEqual(res_user.status_code, 200)
        user_rep = res_user.get_json()
        self.assertIn('statistics', user_rep)

if __name__ == '__main__':
    unittest.main()
