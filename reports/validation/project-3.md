# Validação pós-refatoração — Projeto 3 (task-manager-api)

Smoke test HTTP independente (fora da skill). A mesma lista de 60 requisições foi enviada à aplicação **original** (baseline) e à **refatorada**, ambas com banco recém-criado por `python seed.py`. Os tokens vêm do próprio `POST /login`: `joao@email.com` é admin e `maria@email.com` é usuária comum. O legado ignora o header `Authorization`.

> Gerado em 2026-11-23, depois da nova execução da skill com a regra de autorização corrigida (AP-04: guarda em todas as operações nomeadas na Recommendation).

## Matriz de autorização (AP-04)

| Operação | anônimo | usuário comum (maria) | admin (joao) | Legado (qualquer chamador) |
|---|---|---|---|---|
| `POST /users` com `role: "admin"` | 401 | 403 | 201 | 201 |
| `PUT /users/<id>` alterando `role` | 401 | 403 | 200 | 200 |
| `PUT /users/<id>` alterando `active` | 401 | 403 | 200 | 200 |
| `DELETE /users/<id>` | 401 | 403 | 200 | 200 |
| `PUT /users/<id>` só com `name` (não guardado) | 200 | 200 | 200 | 200 |

## Boot da aplicação refatorada

```
$ python seed.py && python -W default app.py
SECRET_KEY not set; using a random ephemeral key (tokens expire on restart)
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-11-23 15:12:29,691 INFO werkzeug: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
2026-11-23 15:12:29,691 INFO werkzeug: Press CTRL+C to quit
2026-11-23 15:12:30,053 INFO src.controllers.task_controller: Task criada id=11
2026-11-23 15:12:30,065 INFO src.controllers.task_controller: Task atualizada id=11
2026-11-23 15:12:30,072 INFO src.controllers.task_controller: Task deletada id=11
2026-11-23 15:12:30,377 INFO src.controllers.user_controller: Usuário criado id=4
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
| 21 | `GET /users/1` — get user | 200 | 200 | ✅ status igual (campo `password` removido) |
| 22 | `GET /users/999` — get user 404 | 404 | 404 | ✅ igual |
| 23 | `POST /login` — login ok (admin joao) | 200 | 200 | ✅ igual (`password` removido; token assinado e com expiração em vez de `fake-jwt-token-N`) |
| 24 | `POST /login` — login user comum (maria) | 200 | 200 | ✅ igual (token assinado) |
| 25 | `POST /login` — login falha | 401 | 401 | ✅ igual |
| 26 | `POST /users` — create user | 201 | 201 | ✅ status igual (campo `password` removido) |
| 27 | `POST /users` — create user email dup | 409 | 409 | ✅ igual |
| 28 | `POST /users` — create user email invalido | 400 | 400 | ✅ igual |
| 29 | `POST /users` — create user role invalido | 400 | 400 | ✅ igual |
| 30 | `POST /login` — login novo user | 200 | 200 | ✅ igual (token assinado) |
| 31 | `PUT /users/4` — update user nome (anonimo, publico) | 200 | 200 | ✅ status igual (`password` removido; continua público (sem campos privilegiados)) |
| 32 | `PUT /users/999` — update user 404 | 404 | 404 | ✅ igual |
| 33 | `GET /users/1/tasks` — user tasks | 200 | 200 | ✅ igual |
| 34 | `PUT /users/4` — AUTH PUT role anonimo | 200 | 401 | 🔒 troca de `role` exige token de admin → 401 |
| 35 | `PUT /users/4` — AUTH PUT role user comum | 200 | 403 | 🔒 usuário comum → 403 |
| 36 | `PUT /users/4` — AUTH PUT role admin | 200 | 200 | ✅ status igual (admin autorizado: igual ao baseline) |
| 37 | `PUT /users/4` — AUTH PUT active anonimo | 200 | 401 | 🔒 troca de `active` exige token de admin → 401 |
| 38 | `PUT /users/4` — AUTH PUT active user comum | 200 | 403 | 🔒 usuário comum → 403 |
| 39 | `PUT /users/4` — AUTH PUT active admin | 200 | 200 | ✅ status igual (admin autorizado: igual ao baseline) |
| 40 | `POST /users` — AUTH POST admin anonimo | 201 | 401 | 🔒 criação de admin exige token de admin → 401 |
| 41 | `POST /users` — AUTH POST admin user comum | 201 | 403 | 🔒 usuário comum → 403 |
| 42 | `POST /users` — AUTH POST admin admin | 201 | 201 | ✅ status igual (admin autorizado: igual ao baseline) |
| 43 | `POST /users` — create vitima | 201 | 201 | ✅ status igual |
| 44 | `DELETE /users/6` — AUTH DELETE user anonimo | 200 | 401 | 🔒 `DELETE /users/<id>` exige admin → 401 |
| 45 | `DELETE /users/4` — AUTH DELETE user user comum | 200 | 403 | 🔒 usuário comum → 403 (no legado apagava o usuário) |
| 46 | `DELETE /users/4` — AUTH DELETE user admin | 404 | 200 | 🔒 admin autorizado apaga (no legado o usuário já tinha sido apagado pelo comum) |
| 47 | `DELETE /users/999` — AUTH DELETE user 404 admin | 404 | 404 | ✅ igual (igual) |
| 48 | `GET /reports/summary` — reports summary | 200 | 200 | ✅ igual |
| 49 | `GET /reports/user/1` — reports user | 200 | 200 | ✅ igual |
| 50 | `GET /reports/user/999` — reports user 404 | 404 | 404 | ✅ igual |
| 51 | `GET /categories` — list categories | 200 | 200 | ✅ igual |
| 52 | `POST /categories` — create category | 201 | 201 | ✅ igual |
| 53 | `POST /categories` — create category sem nome | 400 | 400 | ✅ igual |
| 54 | `PUT /categories/5` — update category | 200 | 200 | ✅ igual |
| 55 | `PUT /categories/999` — update category 404 | 404 | 404 | ✅ igual |
| 56 | `DELETE /categories/5` — delete category | 200 | 200 | ✅ igual |
| 57 | `GET /tasks/search` — search priority invalida | 500 | 400 | 🔒 500 (ValueError) → 400 |
| 58 | `PUT /categories/1` — update category sem body | 415 | 400 | 🔒 415 HTML do Flask → 400 JSON (`Dados inválidos`) no handler central |
| 59 | `POST /tasks` — create task prioridade texto | 500 | 400 | 🔒 500 (TypeError) → 400 |
| 60 | `GET /nao-existe` — rota inexistente | 404 | 404 | ✅ igual (404 agora em JSON `{"error"}`) |

**48 com o mesmo status do baseline · 12 mudanças intencionais · 0 verificações novas · 0 erros 5xx**
