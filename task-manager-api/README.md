# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Originalmente tinha alguma separação de camadas, mas com problemas arquiteturais e de qualidade; foi refatorado para MVC (veja a seção de arquitetura).

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

O seed não tem senhas fixas: usa `SEED_PASSWORD` (se definida no `.env`) para os três usuários ou gera senhas aleatórias e as imprime no terminal (`joao` = admin, `maria` = user, `pedro` = manager).

## Arquitetura (pós-refatoração)

```
app.py            # create_app(): composition root
config/           # settings.py (única leitura de variáveis de ambiente)
models/           # entidades + regras de domínio (is_overdue, hash de senha)
services/         # regras de negócio e queries (task, user, category, report, notification)
                  # + access_policy.py (autorização por dono/role)
controllers/      # orquestração: request -> validator -> service -> view
validators/       # validação de entrada (400 com mensagens uniformes)
views/            # serializers JSON (nunca expõem password)
routes/           # só mapeia URL -> controller
middlewares/      # auth.py (token assinado), error_handler.py (erros centralizados)
utils/            # constants, errors, clock, stats, request_utils
```

## Configuração

Copie `.env.example` para `.env`. Principais variáveis: `SECRET_KEY`, `DATABASE_URL`, `DEBUG` (padrão `false`), `HOST` (padrão `127.0.0.1`), `PORT`, `CORS_ORIGINS`, `SMTP_*`, `SEED_PASSWORD`.

Sem `SECRET_KEY`, a app gera uma chave aleatória a cada boot (os tokens deixam de valer ao reiniciar). Em produção, defina-a e restrinja `CORS_ORIGINS`.

## Autenticação e controle de acesso

`POST /login` devolve um token assinado. Envie-o em `Authorization: Bearer <token>`. O token vale por `TOKEN_MAX_AGE` segundos e deixa de valer quando a senha do usuário muda.

Roles: `user`, `manager`, `admin`. "Staff" = `admin` ou `manager`.

| Rota | Regra |
|---|---|
| `GET /`, `GET /health` | pública (monitoramento) |
| `POST /login` | pública (login) |
| `POST /users` | pública para registro com role `user`; `role` diferente de `user` ou `active` exigem admin (401 sem token, 403 não-admin) |
| `GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks` | autenticado (expõem e-mail e role) |
| `PUT /users/<id>` | autenticado + próprio usuário ou admin; `role`/`active` só admin, inclusive sobre si |
| `DELETE /users/<id>` | admin |
| `GET /tasks`, `/tasks/<id>`, `/tasks/search`, `/tasks/stats` | pública (quadro de tasks, sem dados sensíveis) |
| `POST /tasks` | autenticado; usuário comum só cria para si (sem `user_id`, a task é dele); staff atribui a qualquer um |
| `PUT /tasks/<id>`, `DELETE /tasks/<id>` | autenticado + dono da task ou staff; reatribuir `user_id` só staff |
| `GET /categories` | pública |
| `POST /categories`, `PUT/DELETE /categories/<id>` | admin |
| `GET /reports/summary` | staff |
| `GET /reports/user/<id>` | próprio usuário ou staff |

Listagens (`/tasks`, `/tasks/search`, `/users`, `/users/<id>/tasks`, `/categories`) aceitam `?limit=` (1–100) e `?offset=` opcionais; sem eles, devolvem tudo como antes.

Senhas novas exigem no mínimo 8 caracteres. Senhas antigas (inclusive MD5) continuam válidas e são migradas para hash seguro no próximo login.
