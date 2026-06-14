# task-manager-api

API de Task Manager em Python/Flask refatorada para o padrão MVC com correções de segurança.

## Estrutura do Projeto

```
task-manager-api/
├── config/
│   └── settings.py          # Configurações lidas de variáveis de ambiente
├── controllers/
│   ├── task_controller.py   # Lógica de negócio de tasks
│   ├── user_controller.py   # Lógica de negócio de usuários + autenticação
│   ├── category_controller.py
│   └── report_controller.py
├── middlewares/
│   ├── auth.py              # Decorator @login_required (JWT)
│   └── error_handler.py     # Handler centralizado de erros
├── models/
│   ├── task.py
│   ├── user.py
│   └── category.py
├── services/
│   └── notification_service.py
├── utils/
│   └── helpers.py
├── views/
│   ├── task_routes.py       # Rotas finas — apenas parse + chamada ao controller
│   ├── user_routes.py
│   ├── category_routes.py
│   └── report_routes.py
├── .env                     # Valores reais (não commitado)
├── .env.example             # Template de variáveis de ambiente
├── app.py                   # Composition root (create_app factory)
├── database.py
├── requirements.txt
└── seed.py
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # edite com seus valores
python seed.py              # popula o banco com dados de exemplo
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`.

> O `seed.py` popula o banco SQLite (`tasks.db`) com 3 usuários, 4 categorias e 10 tasks de exemplo. Rode-o antes do primeiro boot.

## Autenticação

A API usa JWT. Endpoints de escrita (POST, PUT, DELETE) exigem token.

**1. Obter token:**
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "joao@email.com", "password": "1234"}'
```

**2. Usar o token:**
```bash
curl -X POST http://127.0.0.1:5000/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Nova task", "priority": 2}'
```

Endpoints de leitura (GET) são públicos.

## Endpoints

### Tasks
| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/tasks` | — | Lista tasks (suporta `?page=1&per_page=20`) |
| GET | `/tasks/<id>` | — | Detalhe de uma task |
| POST | `/tasks` | JWT | Cria task |
| PUT | `/tasks/<id>` | JWT | Atualiza task |
| DELETE | `/tasks/<id>` | JWT | Remove task |
| GET | `/tasks/search` | — | Busca (`?q=&status=&priority=&user_id=`) |
| GET | `/tasks/stats` | — | Contadores por status + overdue |

### Usuários
| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/users` | — | Lista usuários |
| GET | `/users/<id>` | — | Detalhe + tasks do usuário |
| POST | `/users` | — | Cria usuário |
| PUT | `/users/<id>` | JWT | Atualiza usuário |
| DELETE | `/users/<id>` | JWT | Remove usuário e suas tasks |
| GET | `/users/<id>/tasks` | — | Tasks de um usuário |
| POST | `/login` | — | Retorna JWT |

### Categorias
| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/categories` | — | Lista categorias com contagem de tasks |
| POST | `/categories` | JWT | Cria categoria |
| PUT | `/categories/<id>` | JWT | Atualiza categoria |
| DELETE | `/categories/<id>` | JWT | Remove categoria |

### Relatórios
| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/reports/summary` | — | Resumo geral (status, prioridade, overdue, produtividade) |
| GET | `/reports/user/<id>` | — | Relatório individual de um usuário |

### Sistema
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Versão da API |
| GET | `/health` | Status + timestamp |

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | `dev-only-...` | Chave secreta do Flask |
| `JWT_SECRET_KEY` | `jwt-dev-only-...` | Chave de assinatura JWT |
| `DATABASE_URL` | `sqlite:///tasks.db` | URL do banco de dados |
| `DEBUG` | `False` | Modo debug |
| `HOST` | `127.0.0.1` | Interface de rede |
| `PORT` | `5000` | Porta |
| `JWT_TOKEN_EXPIRES_HOURS` | `24` | Expiração do token em horas |
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |
| `EMAIL_PORT` | `587` | Porta SMTP |
| `EMAIL_USER` | — | Usuário de email |
| `EMAIL_PASSWORD` | — | Senha de email |

## Alterações Realizadas (Refatoração)

### Segurança (CRITICAL)
- **SECRET_KEY** removida do código-fonte — lida via `os.getenv('SECRET_KEY')`
- **Credenciais de email** removidas do `NotificationService` — lidas via env vars
- **Hash MD5** substituído por bcrypt via `werkzeug.security` (`generate_password_hash` / `check_password_hash`)
- **Fake JWT** (`'fake-jwt-token-' + str(user.id)`) substituído por tokens reais com `flask-jwt-extended`
- **`debug=True` hardcoded** removido — lido de `DEBUG` env var, padrão `False`; host padrão `127.0.0.1` em vez de `0.0.0.0`

### Segurança (HIGH)
- **Campo `password` removido de `User.to_dict()`** — nunca mais exposto em respostas de API
- **Autenticação real implementada** — POST/PUT/DELETE protegidos com `@login_required` (JWT)

### Arquitetura
- **Camada `controllers/` criada** — toda lógica de negócio extraída das rotas para controllers dedicados
- **Camada `views/` criada** — rotas reduzidas a 3 linhas (parse → controller → jsonify)
- **`config/settings.py` criado** — configuração centralizada via `Config` class + dotenv
- **`middlewares/` criado** — `auth.py` (decorator JWT) e `error_handler.py` (handlers centralizados)
- **`app.py` usa `create_app()` factory** — composition root limpo, sem lógica de negócio
- **`routes/` removido** — substituído por `views/` seguindo o padrão MVC
- **Categorias separadas** de `report_routes.py` para `views/category_routes.py`

### Qualidade
- **Cálculo de overdue duplicado 6 vezes** substituído pela chamada ao método `task.is_overdue()` do model
- **Serialização manual de tasks** substituída por `task.to_dict()` onde estava sendo duplicada
- **N+1 em `GET /tasks`** eliminado com `joinedload(Task.user, Task.category)`
- **N+1 no relatório de produtividade** eliminado com query de agregação em vez de loop por usuário
- **Paginação adicionada** em `GET /tasks` (parâmetros opcionais `?page=&per_page=`)
- **`except:` bare** substituído por `except SQLAlchemyError` com re-raise ao handler centralizado
- **None check adicionado** em `update_category` antes de acessar o body da requisição
- **Imports não utilizados** removidos de todos os arquivos
- **`MIN_PASSWORD_LENGTH`** aumentado de 4 para 8 caracteres
- **Constantes de `utils/helpers.py`** agora usadas nos controllers em vez de magic numbers inline
