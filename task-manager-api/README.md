# task-manager-api

API de Task Manager em Python/Flask, refatorada para o padrão **MVC + Services + Repositories**.

## Arquitetura

```
task-manager-api/
├── app.py                  # composition root (create_app)
├── config/settings.py      # configuração via variáveis de ambiente
├── errors.py               # exceções de domínio
├── database.py             # instância SQLAlchemy
├── models/                 # entidades e invariantes
├── repositories/           # acesso a dados (queries parametrizadas)
├── services/               # regras de negócio (sem HTTP)
├── controllers/            # orquestração request → service → response
├── routes/                 # somente registro URL → controller
├── validators/             # schemas de validação (marshmallow)
├── middleware/             # error handler central + guard JWT
├── utils/helpers.py        # utilitários sem estado
├── migrations/             # Alembic/Flask-Migrate
└── tests/                  # testes de integração (pytest)
```

Fluxo: `routes` → `controllers` → `services` → `repositories` → `models`.

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # opcional (defaults seguros)
flask --app app db upgrade    # aplica as migrations
python seed.py                # popula dados de exemplo (aplica migrations também)
python app.py                 # sobe em http://127.0.0.1:5000
```

## Configuração

Todas as variáveis estão documentadas em `.env.example`. Principais:

| Variável | Default | Descrição |
|---|---|---|
| `SECRET_KEY` | gerada em boot | Chave de assinatura JWT; defina em produção |
| `DATABASE_URL` | `sqlite:///<projeto>/tasks.db` | Conexão do banco |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Bind do servidor |
| `FLASK_DEBUG` | `false` | Debug da aplicação |
| `AUTH_REQUIRED` | `true` | Auth default deny: exige Bearer JWT em rotas de escrita |
| `JWT_EXPIRATION_SECONDS` | `86400` | Validade do token |

## Autenticação

`POST /login` retorna um **JWT real** assinado com `SECRET_KEY`:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' | jq -r .token)

curl -X POST localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Nova task"}'
```

A autenticação é **default deny** e fail-closed: todas as rotas `POST`/`PUT`/`DELETE` (exceto `/login`) exigem o header, sem depender de flag opt-in. `AUTH_REQUIRED=true` é o default e reflete esse comportamento. Identidade, papel e posse são derivados do JWT; `user_id`/`role` enviados no body não são confiados.

A **gestão de usuários** exige papel `admin`:

- `GET /users` (listagem administrativa)
- `POST /users`
- `PUT /users/<id>`
- `DELETE /users/<id>`

Requisições sem token retornam `401`; tokens de usuários comuns recebem `403`. Usuários não-admin só podem criar, atualizar e remover tarefas das quais são donos; `admin` pode operar sobre qualquer tarefa.

## Testes

```bash
pytest
```

8 testes de integração cobrem todos os recursos, contratos de resposta, validação (400), auth (401/403/201/200), posse de tarefas e migração de hash MD5 legado. A suíte usa `TestConfig` com `AUTH_REQUIRED=True`, sem mascarar o comportamento do default de produção.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Identificação da API |
| GET | `/health` | Health check |
| GET/POST | `/tasks` | Lista/cria tarefas |
| GET/PUT/DELETE | `/tasks/<id>` | Detalha/atualiza/remove tarefa |
| GET | `/tasks/search` | Busca por `q`, `status`, `priority`, `user_id` |
| GET | `/tasks/stats` | Estatísticas agregadas |
| GET/POST | `/users` | Lista (admin) / cria (admin) usuários |
| GET/PUT/DELETE | `/users/<id>` | Detalha (público) / atualiza (admin) / remove (admin) usuário |
| GET | `/users/<id>/tasks` | Tarefas do usuário |
| POST | `/login` | Autenticação (JWT) |
| GET | `/reports/summary` | Relatório geral |
| GET | `/reports/user/<id>` | Relatório por usuário |
| GET/POST | `/categories` | Lista/cria categorias |
| PUT/DELETE | `/categories/<id>` | Atualiza/remove categoria |

## Mudanças de contrato em relação ao projeto original

- Todas as rotas de escrita exigem JWT por padrão (`401` sem token). A gestão de usuários exige `admin` (`403` para os demais).
- Tarefas de não-admin são sempre criadas/atualizadas com o dono derivado do token; criar ou transferir para terceiro retorna `403`.
- `password` (hash) deixou de ser retornado por `/users` e `/login` (correção de segurança).
- `/login` passou a emitir JWT real em vez de `fake-jwt-token-<id>`.
- O banco SQLite passa a ficar na raiz do projeto (`tasks.db`) em vez de `instance/`.
- Erros de validação que antes causavam 500 agora retornam 400 com `{"error": "..."}`.
