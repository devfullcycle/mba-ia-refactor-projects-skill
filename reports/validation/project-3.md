# Validação pós-refatoração — Projeto 3 (task-manager-api)

Smoke test HTTP independente (fora da skill). A mesma lista de 58 requisições foi enviada à aplicação **original** (commit `6d1ce62`) e à **refatorada**, ambas com banco recém-criado por `python seed.py`. Os tokens vêm do próprio `POST /login`: `joao@email.com` (id 1) é admin, `maria@email.com` (id 2) é usuária comum e `pedro@email.com` (id 3) é manager. O legado ignora o header `Authorization`.

> Gerado em 2026-11-27, depois da 3ª execução da skill. A regra 5 do `SKILL.md` e o T-17 passaram a incluir a troca de `password`/`email` de outra conta (permitida só ao próprio usuário ou a um admin).

## Cadeia de account takeover (feedback da 2ª correção)

No legado, qualquer pessoa troca a senha do admin e entra como ele:

| Passo | Legado | Refatorado |
|---|---|---|
| Anônimo: `PUT /users/1 {"password": "hacked1"}` | 200 | **401** |
| `POST /login` como joao com `hacked1` | 200 (token de admin) | **401** |
| maria: `PUT /users/1 {"password": "hacked2"}` | 200 | **403** |
| pedro (manager): `PUT /users/1 {"password": "hacked3"}` | 200 | **403** |
| Anônimo: `PUT /users/1 {"email": "evil@email.com"}` | 200 | **401** |
| maria: `PUT /users/3 {"email": ...}` | 200 | **403** |
| `POST /login` como joao com a senha original `1234` | 401 (senha já sequestrada) | **200** |

## Matriz de autorização (AP-04)

| Operação | anônimo | outro usuário comum | o próprio usuário | admin | Legado (qualquer chamador) |
|---|---|---|---|---|---|
| `POST /users` com `role: "admin"` | 401 | 403 | — | 201 | 201 |
| `PUT /users/<id>` alterando `role` | 401 | 403 | 403 | 200 | 200 |
| `PUT /users/<id>` alterando `active` | 401 | 403 | — | 200 | 200 |
| `PUT /users/<id>` alterando `password` | 401 | 403 | 200 | 200 | 200 |
| `PUT /users/<id>` alterando `email` | 401 | 403 | 200 | 200 | 200 |
| `DELETE /users/<id>` | 401 | 403 | — | 200 | 200 |
| `PUT /users/<id>` só com `name` (não guardado) | 200 | — | — | — | 200 |

Depois da troca feita pelo dono (maria) e pelo admin (senha do pedro), o login com as novas credenciais funciona (200).

## Boot da aplicação refatorada

```
$ python -W default seed.py && python -W default app.py
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
 * Serving Flask app 'src.app'
 * Debug mode: off
INFO werkzeug: WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5057
```

Nenhum `DeprecationWarning`/`LegacyAPIWarning` (`Query.get`, `datetime.utcnow`), que apareciam no legado. Nenhuma resposta contém `password`.

## Antes × depois (todas as requisições)

| # | Request | Antes | Depois | Resultado |
|---|---|---|---|---|
| 1 | `GET /` — root | 200 | 200 | ✅ igual |
| 2 | `GET /health` — health | 200 | 200 | ✅ igual |
| 3 | `POST /login` — login admin joao | 200 | 200 | ✅ igual |
| 4 | `POST /login` — login user maria | 200 | 200 | ✅ igual |
| 5 | `POST /login` — login manager pedro | 200 | 200 | ✅ igual |
| 6 | `POST /login` — login wrong password | 401 | 401 | ✅ igual |
| 7 | `POST /login` — login missing fields | 400 | 400 | ✅ igual |
| 8 | `GET /users` — list users | 200 | 200 | ✅ igual |
| 9 | `GET /users/1` — get user 1 | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 10 | `GET /users/999` — get user 404 | 404 | 404 | ✅ igual |
| 11 | `GET /users/1/tasks` — user tasks | 200 | 200 | ✅ igual |
| 12 | `POST /users` — signup regular user | 201 | 201 | ✅ status igual (sem `password` na resposta) |
| 13 | `POST /users` — signup duplicate email | 409 | 409 | ✅ igual |
| 14 | `POST /users` — signup invalid email | 400 | 400 | ✅ igual |
| 15 | `POST /users` — signup short password | 400 | 400 | ✅ igual |
| 16 | `GET /tasks` — list tasks | 200 | 200 | ✅ igual |
| 17 | `GET /tasks/1` — get task 1 | 200 | 200 | ✅ igual |
| 18 | `GET /tasks/999` — get task 404 | 404 | 404 | ✅ igual |
| 19 | `POST /tasks` — create task | 201 | 201 | ✅ igual |
| 20 | `POST /tasks` — create task no title | 400 | 400 | ✅ igual |
| 21 | `PUT /tasks/11` — update task | 200 | 200 | ✅ igual |
| 22 | `GET /tasks/search` — search tasks | 200 | 200 | ✅ igual |
| 23 | `GET /tasks/stats` — task stats | 200 | 200 | ✅ igual |
| 24 | `DELETE /tasks/11` — delete task | 200 | 200 | ✅ igual |
| 25 | `GET /categories` — list categories | 200 | 200 | ✅ igual |
| 26 | `POST /categories` — create category | 201 | 201 | ✅ igual |
| 27 | `PUT /categories/5` — update category | 200 | 200 | ✅ igual |
| 28 | `DELETE /categories/5` — delete category | 200 | 200 | ✅ igual |
| 29 | `GET /reports/summary` — report summary | 200 | 200 | ✅ igual |
| 30 | `GET /reports/user/1` — report user 1 | 200 | 200 | ✅ igual |
| 31 | `PUT /users/2` — PUT name only anonymous | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 32 | `PUT /users/1` — TAKEOVER anonymous sets admin password | 200 | 401 | 🔒 guarda: anônimo → 401 |
| 33 | `POST /login` — TAKEOVER login admin with hacked password (anon) | 200 | 401 | 🔒 a senha do admin não foi trocada |
| 34 | `PUT /users/1` — TAKEOVER user maria sets admin password | 200 | 403 | 🔒 guarda: sem permissão → 403 |
| 35 | `POST /login` — TAKEOVER login admin with hacked password (maria) | 200 | 401 | 🔒 a senha do admin não foi trocada |
| 36 | `PUT /users/1` — TAKEOVER manager pedro sets admin password | 200 | 403 | 🔒 guarda: sem permissão → 403 |
| 37 | `PUT /users/1` — TAKEOVER anonymous changes admin email | 200 | 401 | 🔒 guarda: anônimo → 401 |
| 38 | `PUT /users/3` — TAKEOVER maria changes pedro email | 200 | 403 | 🔒 guarda: sem permissão → 403 |
| 39 | `POST /login` — login admin original password still works | 401 | 200 | 🔒 no legado a senha original já tinha sido sequestrada |
| 40 | `PUT /users/2` — OWNER maria changes own password | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 41 | `POST /login` — OWNER maria logs in with new password | 200 | 200 | ✅ igual |
| 42 | `PUT /users/2` — OWNER maria changes own email | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 43 | `PUT /users/3` — ADMIN changes pedro password | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 44 | `PUT /users/3` — ADMIN changes pedro email | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 45 | `POST /login` — pedro logs in with admin-set credentials | 200 | 200 | ✅ igual |
| 46 | `PUT /users/2` — AUTH role change anonymous | 200 | 401 | 🔒 guarda: anônimo → 401 |
| 47 | `PUT /users/2` — AUTH role change self (maria) | 200 | 403 | 🔒 guarda: sem permissão → 403 |
| 48 | `PUT /users/2` — AUTH role change admin | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 49 | `PUT /users/4` — AUTH active change anonymous | 200 | 401 | 🔒 guarda: anônimo → 401 |
| 50 | `PUT /users/4` — AUTH active change maria | 200 | 403 | 🔒 guarda: sem permissão → 403 |
| 51 | `PUT /users/4` — AUTH active change admin | 200 | 200 | ✅ status igual (sem `password` na resposta) |
| 52 | `POST /users` — AUTH admin signup anonymous | 201 | 401 | 🔒 guarda: anônimo → 401 |
| 53 | `POST /users` — AUTH admin signup maria | 201 | 403 | 🔒 guarda: sem permissão → 403 |
| 54 | `POST /users` — AUTH admin signup admin | 201 | 201 | ✅ status igual (sem `password` na resposta) |
| 55 | `DELETE /users/4` — AUTH delete user anonymous | 200 | 401 | 🔒 guarda: anônimo → 401 |
| 56 | `DELETE /users/4` — AUTH delete user maria | 404 | 403 | 🔒 guarda: sem permissão → 403 |
| 57 | `DELETE /users/4` — AUTH delete user admin | 404 | 200 | 🔒 no legado o anônimo já tinha apagado o usuário |
| 58 | `DELETE /users/999` — delete user 404 admin | 404 | 404 | ✅ igual |

**41 com o mesmo status do baseline · 17 mudanças intencionais · 0 verificações novas · 0 erros 5xx**
