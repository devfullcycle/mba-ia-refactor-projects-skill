# task-manager-api

API de Task Manager em Python/Flask, refatorada para MVC pela skill `refactor-arch` (auditoria em `../reports/audit-project-3.md`).

## Estrutura

```text
app.py / seed.py        # Entrypoints de compatibilidade (python app.py / python seed.py)
src/
├── app.py              # Application factory create_app()
├── config/             # settings.py (.env), database.py (SQLAlchemy + PRAGMA foreign_keys), seed.py
├── models/             # Entidades e consultas: task.py, user.py, category.py
├── controllers/        # Validação, regras de negócio e autorização por recurso
├── routes/             # Blueprints finos (mesmos paths e métodos do legado)
├── middlewares/        # auth.py (Bearer token, perfis), error_handler.py (erros JSON)
├── services/           # auth_service.py (token assinado), notification_service.py (SMTP opcional)
└── utils/              # errors, validators, pagination, dates
tests/                  # pytest
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # defina SECRET_KEY e as senhas SEED_*
python app.py             # com SEED_DB=true o banco vazio é populado no boot
```

`python seed.py` popula um banco vazio; `python seed.py --reset` apaga e recria os dados de exemplo. O seed nunca roda com `APP_ENV=production`. Se uma senha `SEED_*` não for definida, ela é gerada e exibida uma vez no log.

O banco padrão é `instance/tasks.db`, o mesmo arquivo da versão legada. Senhas MD5 antigas são regravadas com hash seguro no primeiro login bem-sucedido.

## Autenticação

`POST /login` devolve `{message, user, token}`. Envie `Authorization: Bearer <token>` nas demais rotas.

| Acesso | Endpoints |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login`, `POST /users` (cadastro sempre com `role=user`) |
| Autenticado | `GET /tasks*`, `POST /tasks`, `GET /users*`, `GET /categories`, `GET /reports/user/<id>` (próprio) |
| Dono da task ou admin/manager | `PUT/DELETE /tasks/<id>` |
| Próprio usuário ou admin | `PUT /users/<id>` (`role`/`active` só admin) |
| admin/manager | `POST/PUT/DELETE /categories`, `GET /reports/summary`, relatórios de outros usuários |
| admin | `DELETE /users/<id>`, criar usuários com outro `role` |

As listagens `GET /tasks`, `/tasks/search` e `/users` aceitam `?page=&per_page=` (opcional; o total volta no header `X-Total-Count`).

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```
