"""Testes de integração dos contratos HTTP e do gate de segurança."""

import hashlib

import pytest

from app import create_app
from config.settings import TestConfig
from database import db
from models.user import User

ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123'
USER_EMAIL = 'ana@example.com'
USER_PASSWORD = 'secret123'
OTHER_EMAIL = 'bruno@example.com'
OTHER_PASSWORD = 'secret123'


def _add_user(name, email, password, role='user'):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    return user


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        _add_user('Admin', ADMIN_EMAIL, ADMIN_PASSWORD, role='admin')
        _add_user('Ana', USER_EMAIL, USER_PASSWORD)
        _add_user('Bruno', OTHER_EMAIL, OTHER_PASSWORD)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email, password):
    response = client.post('/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return response.get_json()['token']


@pytest.fixture
def admin_token(client):
    return _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture
def user_token(client):
    return _login(client, USER_EMAIL, USER_PASSWORD)


@pytest.fixture
def other_token(client):
    return _login(client, OTHER_EMAIL, OTHER_PASSWORD)


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def create_user(client, token, **overrides):
    payload = {
        'name': 'Novo',
        'email': 'novo@example.com',
        'password': 'secret123',
        **overrides,
    }
    return client.post('/users', json=payload, headers=auth(token))


def create_category(client, token, **overrides):
    payload = {'name': 'Backend', 'color': '#3498db', **overrides}
    return client.post('/categories', json=payload, headers=auth(token))


def test_health_and_index(client):
    assert client.get('/health').status_code == 200
    body = client.get('/').get_json()
    assert body['message'] == 'Task Manager API'


def test_user_management_requires_admin_and_no_password_leak(
    client, admin_token, user_token
):
    anonymous = client.post('/users', json={
        'name': 'Anon', 'email': 'anon@example.com', 'password': 'secret123',
    })
    assert anonymous.status_code == 401

    forbidden = create_user(client, user_token)
    assert forbidden.status_code == 403

    response = create_user(client, admin_token)
    assert response.status_code == 201
    user = response.get_json()
    assert 'password' not in user
    user_id = user['id']

    assert client.get('/users').status_code == 401
    assert client.get('/users', headers=auth(user_token)).status_code == 403
    admin_list = client.get('/users', headers=auth(admin_token))
    assert admin_list.status_code == 200
    assert any(item['id'] == user_id for item in admin_list.get_json())

    assert client.get(f'/users/{user_id}').status_code == 200

    denied_update = client.put(
        f'/users/{user_id}', json={'name': 'Nope'}, headers=auth(user_token)
    )
    assert denied_update.status_code == 403

    updated = client.put(
        f'/users/{user_id}', json={'name': 'Novo Nome'}, headers=auth(admin_token)
    )
    assert updated.status_code == 200
    assert updated.get_json()['name'] == 'Novo Nome'

    duplicate = create_user(client, admin_token)
    assert duplicate.status_code == 409

    assert client.get(f'/users/{user_id}/tasks').get_json() == []

    denied_delete = client.delete(f'/users/{user_id}', headers=auth(user_token))
    assert denied_delete.status_code == 403

    assert client.delete(f'/users/{user_id}', headers=auth(admin_token)).status_code == 200
    assert client.get(f'/users/{user_id}').status_code == 404


def test_login_returns_jwt(client):
    response = client.post('/login', json={
        'email': USER_EMAIL,
        'password': USER_PASSWORD,
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body['token'].count('.') == 2
    assert 'password' not in body['user']

    assert client.post('/login', json={
        'email': USER_EMAIL,
        'password': 'wrong',
    }).status_code == 401


def test_tasks_flow_relations_and_ownership(
    client, admin_token, user_token, other_token
):
    category_id = create_category(client, user_token).get_json()['id']

    created = client.post('/tasks', json={
        'title': 'Escrever testes',
        'description': 'Cobrir endpoints',
        'priority': 1,
        'category_id': category_id,
        'due_date': '2020-01-01',
        'tags': ['qa', 'backend'],
    }, headers=auth(user_token))
    assert created.status_code == 201
    task = created.get_json()
    task_id = task['id']
    assert task['tags'] == ['qa', 'backend']

    users = client.get('/users', headers=auth(admin_token)).get_json()
    ana_id = next(item['id'] for item in users if item['email'] == USER_EMAIL)
    other_id = next(item['id'] for item in users if item['email'] == OTHER_EMAIL)
    assert task['user_id'] == ana_id

    listed = client.get('/tasks').get_json()
    assert listed[0]['user_name'] == 'Ana'
    assert listed[0]['category_name'] == 'Backend'
    assert listed[0]['overdue'] is True

    assert client.get(f'/tasks/{task_id}').status_code == 200
    assert client.get('/tasks/search?q=testes').get_json()[0]['id'] == task_id
    assert client.get('/tasks/stats').get_json()['overdue'] == 1

    updated = client.put(
        f'/tasks/{task_id}',
        json={'status': 'done', 'due_date': None},
        headers=auth(user_token),
    )
    assert updated.status_code == 200
    assert updated.get_json()['status'] == 'done'

    assert client.put(
        f'/tasks/{task_id}', json={'title': 'Invasão'}, headers=auth(other_token)
    ).status_code == 403
    assert client.delete(f'/tasks/{task_id}', headers=auth(other_token)).status_code == 403

    assert client.post('/tasks', json={
        'title': 'Tarefa alheia',
        'user_id': other_id,
    }, headers=auth(user_token)).status_code == 403

    assert client.delete(f'/tasks/{task_id}', headers=auth(user_token)).status_code == 200
    assert client.get(f'/tasks/{task_id}').status_code == 404


def test_categories_and_reports(client, user_token):
    category_id = create_category(client, user_token).get_json()['id']
    created = client.post('/tasks', json={
        'title': 'Task A',
        'category_id': category_id,
    }, headers=auth(user_token))
    assert created.status_code == 201

    categories = client.get('/categories').get_json()
    assert categories[0]['task_count'] == 1

    assert client.put(
        f'/categories/{category_id}', json={'name': 'API'}, headers=auth(user_token)
    ).status_code == 200
    assert client.delete(
        f'/categories/{category_id}', headers=auth(user_token)
    ).status_code == 200

    summary = client.get('/reports/summary')
    assert summary.status_code == 200
    body = summary.get_json()
    assert body['overview']['total_tasks'] == 1
    ana_id = created.get_json()['user_id']
    ana_stats = next(
        item for item in body['user_productivity'] if item['user_id'] == ana_id
    )
    assert ana_stats['total_tasks'] == 1
    assert body['tasks_by_priority']['critical'] == 0

    assert client.get(f'/reports/user/{ana_id}').status_code == 200


def test_invalid_payloads_return_400(client, admin_token, user_token):
    headers = auth(user_token)

    assert client.post('/tasks', json={}, headers=headers).status_code == 400
    assert client.post('/tasks', json={'title': 'ab'}, headers=headers).status_code == 400
    assert client.post(
        '/tasks', json={'title': 'Titulo', 'priority': 9}, headers=headers
    ).status_code == 400
    assert client.post(
        '/tasks', json={'title': 'Titulo', 'due_date': 'not-a-date'}, headers=headers
    ).status_code == 400
    assert client.post('/users', json={
        'name': 'Ana', 'email': 'bad', 'password': 'x',
    }, headers=auth(admin_token)).status_code == 400
    assert client.post('/categories', json={}, headers=headers).status_code == 400
    assert client.post(
        '/tasks', data='not json', content_type='text/plain', headers=headers
    ).status_code == 400

    category_id = create_category(client, user_token).get_json()['id']
    assert client.put(
        f'/categories/{category_id}', json=None, headers=headers
    ).status_code == 400


def test_security_gate_401_403_and_authorized_paths(
    client, admin_token, user_token
):
    # POST /tasks
    assert client.post('/tasks', json={'title': 'Sem token'}).status_code == 401
    assert client.post(
        '/tasks', json={'title': 'Com token'}, headers=auth(user_token)
    ).status_code == 201

    # POST /users
    new_user = {
        'name': 'Gate', 'email': 'gate@example.com', 'password': 'secret123',
    }
    assert client.post('/users', json=new_user).status_code == 401
    assert client.post(
        '/users', json=new_user, headers=auth(user_token)
    ).status_code == 403
    created = client.post('/users', json=new_user, headers=auth(admin_token))
    assert created.status_code == 201
    target_id = created.get_json()['id']

    # PUT/DELETE /users/<id>
    assert client.put(
        f'/users/{target_id}', json={'name': 'X'}, headers=auth(user_token)
    ).status_code == 403
    assert client.delete(
        f'/users/{target_id}', headers=auth(user_token)
    ).status_code == 403
    assert client.put(
        f'/users/{target_id}', json={'name': 'Admin Edit'}, headers=auth(admin_token)
    ).status_code == 200
    assert client.delete(
        f'/users/{target_id}', headers=auth(admin_token)
    ).status_code == 200

    # Listagem administrativa
    assert client.get('/users').status_code == 401
    assert client.get('/users', headers=auth(user_token)).status_code == 403
    assert client.get('/users', headers=auth(admin_token)).status_code == 200

    # /login permanece público
    assert client.post('/login', json={
        'email': USER_EMAIL,
        'password': USER_PASSWORD,
    }).status_code == 200


def test_legacy_md5_password_is_rehashed_on_login(app, client):
    legacy = User(name='Legacy', email='legacy@example.com', role='user')
    legacy.password = hashlib.md5(b'oldpass').hexdigest()
    db.session.add(legacy)
    db.session.commit()

    assert client.post('/login', json={
        'email': 'legacy@example.com',
        'password': 'oldpass',
    }).status_code == 200

    stored = User.query.filter_by(email='legacy@example.com').first().password
    assert not User._is_legacy_md5(stored)
