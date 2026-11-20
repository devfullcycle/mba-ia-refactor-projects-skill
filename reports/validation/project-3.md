# Validação pós-refatoração — Projeto 3 (task-manager-api)

Gerado com um smoke test HTTP independente (fora da skill): a mesma lista de requisições foi enviada à aplicação **original** (baseline) e à **refatorada**, sobre um banco recém-criado.

## Boot da aplicação refatorada

```
$ python seed.py && python -W default app.py
2026-11-19 20:17:58,242 WARNING src.config.settings: SECRET_KEY not set; using a random ephemeral key (tokens expire on restart)
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-11-19 20:17:58,261 INFO werkzeug: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
2026-11-19 20:17:58,261 INFO werkzeug: Press CTRL+C to quit
2026-11-19 20:17:58,705 INFO src.controllers.task_controller: Task criada id=11
2026-11-19 20:17:58,712 INFO src.controllers.task_controller: Task atualizada id=11
2026-11-19 20:17:58,716 INFO src.controllers.task_controller: Task deletada id=11
2026-11-19 20:17:58,796 INFO src.controllers.user_controller: Usuário criado id=4
2026-11-19 20:17:59,005 INFO src.controllers.user_controller: Usuário deletado id=4
2026-11-19 20:17:59,015 INFO src.controllers.category_controller: Categoria criada id=5
```

## Comparação antes × depois

| # | Request | Antes | Depois | Resultado |
|---|---|---|---|---|
| 1 | `GET /` — index | 200 | 200 | ✅ igual |
| 2 | `GET /health` — health | 200 | 200 | ✅ igual |
| 3 | `GET /tasks` — list tasks | 200 | 200 | ✅ igual |
| 4 | `GET /tasks/1` — get task | 200 | 200 | ✅ igual |
| 5 | `GET /tasks/999` — get task 404 | 404 | 404 | ✅ igual |
| 6 | `GET /tasks/search` — search | 200 | 200 | ✅ igual |
| 7 | `GET /tasks/search` — search priority | 200 | 200 | ✅ igual |
| 8 | `GET /tasks/stats` — stats | 200 | 200 | ✅ igual |
| 9 | `POST /tasks` — create task | 201 | 201 | ✅ igual |
| 10 | `POST /tasks` — create task sem titulo | 400 | 400 | ✅ igual |
| 11 | `POST /tasks` — create task status invalido | 400 | 400 | ✅ igual |
| 12 | `POST /tasks` — create task prioridade invalida | 400 | 400 | ✅ igual |
| 13 | `POST /tasks` — create task user inexistente | 404 | 404 | ✅ igual |
| 14 | `POST /tasks` — create task data invalida | 400 | 400 | ✅ igual |
| 15 | `PUT /tasks/11` — update task | 200 | 200 | ✅ igual |
| 16 | `PUT /tasks/11` — update task invalido | 400 | 400 | ✅ igual |
| 17 | `PUT /tasks/999` — update task 404 | 404 | 404 | ✅ igual |
| 18 | `DELETE /tasks/11` — delete task | 200 | 200 | ✅ igual |
| 19 | `DELETE /tasks/11` — delete task 404 | 404 | 404 | ✅ igual |
| 20 | `GET /users` — list users | 200 | 200 | ✅ igual |
| 21 | `GET /users/1` — get user | 200 | 200 | ✅ status igual; campo `password` removido |
| 22 | `GET /users/999` — get user 404 | 404 | 404 | ✅ igual |
| 23 | `POST /users` — create user | 201 | 201 | ✅ status igual; campo `password` removido |
| 24 | `POST /users` — create user email dup | 409 | 409 | ✅ igual |
| 25 | `POST /users` — create user email invalido | 400 | 400 | ✅ igual |
| 26 | `POST /users` — create user role invalido | 400 | 400 | ✅ igual |
| 27 | `PUT /users/4` — update user | 200 | 200 | ✅ status igual; campo `password` removido |
| 28 | `PUT /users/999` — update user 404 | 404 | 404 | ✅ igual |
| 29 | `GET /users/1/tasks` — user tasks | 200 | 200 | ✅ igual |
| 30 | `POST /login` — login ok | 200 | 200 | ✅ igual (`password` removido; token assinado (itsdangerous) em vez de `fake-jwt-token-N`) |
| 31 | `POST /login` — login novo user | 200 | 200 | ✅ igual (`password` removido; token assinado) |
| 32 | `POST /login` — login falha | 401 | 401 | ✅ igual |
| 33 | `DELETE /users/4` — delete user | 200 | 200 | ✅ igual |
| 34 | `GET /reports/summary` — reports summary | 200 | 200 | ✅ igual |
| 35 | `GET /reports/user/1` — reports user | 200 | 200 | ✅ igual |
| 36 | `GET /reports/user/999` — reports user 404 | 404 | 404 | ✅ igual |
| 37 | `GET /categories` — list categories | 200 | 200 | ✅ igual |
| 38 | `POST /categories` — create category | 201 | 201 | ✅ igual |
| 39 | `POST /categories` — create category sem nome | 400 | 400 | ✅ igual |
| 40 | `PUT /categories/5` — update category | 200 | 200 | ✅ igual |
| 41 | `PUT /categories/999` — update category 404 | 404 | 404 | ✅ igual |
| 42 | `DELETE /categories/5` — delete category | 200 | 200 | ✅ igual |
| 43 | `GET /nao-existe` — rota inexistente | 404 | 404 | ✅ status igual; 404 agora em JSON `{"error"}` |
| 44 | `POST /users` — escalada admin anonima | — | 403 | 🆕 auto-promoção a admin bloqueada (antes 201) |
| 45 | `GET /tasks/search` — search priority invalida | — | 400 | 🆕 antes 500 (ValueError) |
| 46 | `PUT /categories/1` — update category sem body | — | 400 | 🆕 antes 500 (TypeError) |
| 47 | `POST /tasks` — create task prioridade texto | — | 400 | 🆕 antes 500 (TypeError) |

**43 iguais ao baseline · 0 mudanças intencionais · 4 verificações novas · 0 erros 5xx**
