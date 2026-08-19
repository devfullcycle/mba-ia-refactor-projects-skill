import unittest
import json
from datetime import datetime, timezone, timedelta
from app import app, db
from models.user import User
from models.category import Category
from models.task import Task

class TaskManagerApiTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        # Create context and database
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        
        # Seed test data
        self.seed_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def seed_test_data(self):
        # Users
        self.u1 = User(name='Test User', email='test@user.com', role='user')
        self.u1.set_password('pass123')
        db.session.add(self.u1)
        
        # Categories
        self.c1 = Category(name='Work', description='Work tasks', color='#00ff00')
        db.session.add(self.c1)
        db.session.commit()
        
        # Tasks
        # 1. Overdue Task
        self.t1 = Task(
            title='Overdue Task',
            description='This is overdue',
            status='pending',
            priority=2,
            user_id=self.u1.id,
            category_id=self.c1.id,
            due_date=datetime.now(timezone.utc) - timedelta(days=2)
        )
        # 2. Future Task
        self.t2 = Task(
            title='Future Task',
            description='This is not overdue',
            status='pending',
            priority=3,
            user_id=self.u1.id,
            category_id=self.c1.id,
            due_date=datetime.now(timezone.utc) + timedelta(days=5)
        )
        db.session.add_all([self.t1, self.t2])
        db.session.commit()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)

    def test_get_users(self):
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test User')

    def test_get_user_tasks_and_serialization(self):
        # Test endpoint /users/<id>/tasks
        response = self.client.get(f'/users/{self.u1.id}/tasks')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        
        # Verify that serialization is using to_dict() and contains 'overdue'
        task_overdue = next(t for t in data if t['title'] == 'Overdue Task')
        task_future = next(t for t in data if t['title'] == 'Future Task')
        
        self.assertTrue(task_overdue['overdue'])
        self.assertFalse(task_future['overdue'])
        
        # Ensure 'updated_at' and 'tags' are serialized since it uses to_dict() now
        self.assertIn('updated_at', task_overdue)
        self.assertIn('tags', task_overdue)

    def test_reports_summary(self):
        response = self.client.get('/reports/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('overview', data)
        self.assertEqual(data['overview']['total_tasks'], 2)
        self.assertEqual(data['overview']['total_users'], 1)
        self.assertEqual(data['overview']['total_categories'], 1)
        
        self.assertIn('overdue', data)
        self.assertEqual(data['overdue']['count'], 1)
        self.assertEqual(data['overdue']['tasks'][0]['title'], 'Overdue Task')

if __name__ == '__main__':
    unittest.main()
