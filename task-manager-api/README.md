# task-manager-api — Task Manager API

API de gerenciamento de tarefas em Python/Flask com arquitetura MVC, usuários, categorias e relatórios.

## Stack
- Python 3 + Flask 3.0 + flask-sqlalchemy 3.1 + flask-cors 4.0
- SQLAlchemy ORM + SQLite (`tasks.db`)
- werkzeug.security (password hashing)

## Como rodar
```bash
pip install -r requirements.txt
cp .env.example .env              # Configure as variáveis de ambiente
python seed.py                    # Popula o banco com dados iniciais
python app.py                     # Inicia o servidor em http://localhost:5000
```

## Estrutura do projeto
```
app.py                            # Entry point (composition root)
config.py                         # Configuração via variáveis de ambiente
database.py                       # Instância SQLAlchemy
seed.py                           # Script de seed
requirements.txt
.env.example                      # Template de variáveis de ambiente
models/
  __init__.py
  user.py                         # Model User (werkzeug hashing, to_dict sem senha)
  task.py                         # Model Task (is_overdue centralizado)
  category.py                     # Model Category
controllers/
  __init__.py
  task_controller.py              # Lógica de negócio de tasks
  user_controller.py              # Lógica de negócio de users + autenticação
  category_controller.py          # Lógica de negócio de categorias
  report_controller.py            # Lógica de relatórios
routes/
  __init__.py
  task_routes.py                  # Endpoints de tasks
  user_routes.py                  # Endpoints de users + login
  category_routes.py              # Endpoints de categorias
  report_routes.py                # Endpoints de relatórios
services/
  __init__.py
  notification_service.py         # Envio de email (SMTP via env vars)
middlewares/
  __init__.py                     # Error handling centralizado
utils/
  __init__.py
  helpers.py                      # Constantes e funções de validação
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

### Categories
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/categories` | Listar categorias (com task_count) |
| POST | `/categories` | Criar categoria |
| PUT | `/categories/<id>` | Atualizar categoria |
| DELETE | `/categories/<id>` | Deletar categoria |

### Reports
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/reports/summary` | Relatório geral (status, prioridade, overdue, produtividade) |
| GET | `/reports/user/<id>` | Relatório por usuário |

### Outros
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Info da API |
| GET | `/health` | Health check |

## Modelos SQLAlchemy
- `users` (id, name, email, password, role, active, created_at)
- `tasks` (id, title, description, status, priority, user_id, category_id, created_at, updated_at, due_date, tags)
- `categories` (id, name, description, color, created_at)

## Variáveis de ambiente
| Variável | Descrição | Default |
|----------|-----------|---------|
| `SECRET_KEY` | Chave secreta da aplicação | dev-secret-key-change-in-production |
| `FLASK_DEBUG` | Modo debug | false |
| `HOST` | Host do servidor | 0.0.0.0 |
| `PORT` | Porta do servidor | 5000 |
| `DATABASE_URL` | String de conexão | sqlite:///tasks.db |
| `SMTP_HOST` | Servidor SMTP | smtp.gmail.com |
| `SMTP_PORT` | Porta SMTP | 587 |
| `SMTP_USER` | Usuário SMTP | (vazio) |
| `SMTP_PASSWORD` | Senha SMTP | (vazio) |
