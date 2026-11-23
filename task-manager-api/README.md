# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possuía alguma separação de camadas; após o `refactor-arch` segue o padrão MVC (`src/config`, `src/models`, `src/controllers`, `src/views`, `src/services`, `src/middlewares`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste SECRET_KEY, HOST, PORT, SMTP_*
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

Por padrão o servidor escuta em `127.0.0.1` com debug desligado; use `HOST=0.0.0.0` e `FLASK_DEBUG=true` apenas em desenvolvimento.

## Autenticação

`POST /login` devolve um `token` assinado e com expiração. Envie-o como `Authorization: Bearer <token>`. Exigem um usuário `admin`:

- `POST /users` com `role` `admin` ou `manager`
- `PUT /users/<id>` quando o corpo altera `role` ou `active`
- `DELETE /users/<id>`

Usuário admin do seed: `joao@email.com` / `1234`.
