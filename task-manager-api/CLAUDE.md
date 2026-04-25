# task-manager-api — Task Manager API

Python/Flask API de gerenciamento de tarefas com usuários, categorias e relatórios.

## Stack
- Python 3 + Flask 3.0 + flask-sqlalchemy 3.1 + flask-cors 4.0
- SQLAlchemy ORM + SQLite (`tasks.db`)
- marshmallow 3.20 (listado mas não utilizado)

## Como rodar
```bash
pip install -r requirements.txt
python app.py          # Inicia o servidor
python seed.py         # Popula o banco com dados iniciais
# Roda em http://localhost:5000
```

## Estrutura atual
```
app.py                            # Entry point, config, registra blueprints
database.py                       # Instância SQLAlchemy (db = SQLAlchemy())
seed.py                           # Script de seed com dados de exemplo
requirements.txt                  # Dependências
models/
  __init__.py
  task.py                         # Model Task (status, priority, due_date, tags)
  user.py                         # Model User (auth, md5 passwords)
  category.py                     # Model Category
routes/
  __init__.py
  task_routes.py                  # CRUD de tasks + search + stats
  user_routes.py                  # CRUD de users + login
  report_routes.py                # Relatórios + CRUD de categorias
services/
  __init__.py
  notification_service.py         # Envio de email (SMTP hardcoded)
utils/
  __init__.py
  helpers.py                      # Funções utilitárias + constantes
```

## Endpoints

### Tasks
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/tasks` | Listar todas tasks (com user_name, category_name, overdue) |
| GET | `/tasks/<id>` | Buscar task por ID |
| POST | `/tasks` | Criar task |
| PUT | `/tasks/<id>` | Atualizar task |
| DELETE | `/tasks/<id>` | Deletar task |
| GET | `/tasks/search?q=&status=&priority=&user_id=` | Buscar tasks |
| GET | `/tasks/stats` | Estatísticas de tasks |

### Users
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/users` | Listar usuários |
| GET | `/users/<id>` | Buscar usuário (com tasks) |
| POST | `/users` | Criar usuário |
| PUT | `/users/<id>` | Atualizar usuário |
| DELETE | `/users/<id>` | Deletar usuário (e suas tasks) |
| GET | `/users/<id>/tasks` | Tasks de um usuário |
| POST | `/login` | Login (email + senha) |

### Reports & Categories
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/reports/summary` | Relatório geral (status, prioridade, overdue, produtividade) |
| GET | `/reports/user/<id>` | Relatório por usuário |
| GET | `/categories` | Listar categorias |
| POST | `/categories` | Criar categoria |
| PUT | `/categories/<id>` | Atualizar categoria |
| DELETE | `/categories/<id>` | Deletar categoria |

### Outros
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Info da API |
| GET | `/health` | Health check |

## Modelos SQLAlchemy
- `users` (id, name, email, password, role, active, created_at)
- `tasks` (id, title, description, status, priority, user_id, category_id, created_at, updated_at, due_date, tags)
- `categories` (id, name, description, color, created_at)

## Organização atual
Possui separação parcial em camadas (models/, routes/, services/, utils/), mas:
- **Controllers inexistentes** — lógica de negócio está nos routes
- **Services subutilizados** — NotificationService existe mas credenciais hardcoded
- **Duplicação** — lógica de overdue copiada em 3 arquivos de routes

## Problemas conhecidos (análise manual)
- Hardcoded SECRET_KEY e credenciais SMTP
- MD5 para hashing de senhas (weak cryptography)
- `to_dict()` do User retorna campo password
- Token JWT falso (`fake-jwt-token-{id}`)
- `datetime.utcnow()` deprecated (Python 3.12+)
- `User.query.get()` deprecated (SQLAlchemy 2.x)
- Lógica de overdue duplicada em 3 routes
- N+1 queries nos relatórios
- Múltiplos bare `except:`
- debug=True em produção
- Imports não utilizados
