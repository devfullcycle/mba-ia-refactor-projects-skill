# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para MVC (`src/config`, `src/models`, `src/controllers`, `src/views`, `src/services`, `src/middlewares`, composition root em `src/app.py`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: defina SECRET_KEY, CORS_ORIGINS, SMTP_*
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Autenticação

`POST /login` devolve um `token` assinado e com expiração. Envie-o como `Authorization: Bearer <token>` nas operações protegidas:

| Operação | Quem pode |
|---|---|
| `POST /users` com `role` diferente de `"user"` | admin |
| `PUT /users/<id>` alterando `role` ou `active` | admin |
| `PUT /users/<id>` alterando `password` ou `email` | o próprio usuário ou admin |
| `DELETE /users/<id>` | admin |

Sem token válido: `401`; autenticado sem permissão: `403`. Demais endpoints continuam públicos.
