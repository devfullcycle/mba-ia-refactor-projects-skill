================================
VALIDATION EVIDENCE — task-manager-api
================================
Date:  2026-07-13 23:22 (local)
Stack: Python (CPython 3.13) + Flask 3.0.0
Port:  5001 (5000 estava ocupada pelo AirPlay Receiver do macOS; porta configurável via env PORT)

## Boot
$ pip install -r requirements.txt      # deps já resolvidas no .venv
$ python seed.py                        # re-seed: 3 usuários, 4 categorias, 10 tasks (senhas com hash werkzeug)
$ PORT=5001 python app.py
[log]  * Serving Flask app 'app'
[log]  * Debug mode: off
[log]  * Running on http://127.0.0.1:5001
[log] 127.0.0.1 - - [13/Jul/2026 20:20:33] "GET /health HTTP/1.1" 200 -
Boot: ✓ OK (sem stack trace; debug desligado por padrão via config)

## Endpoints
| Método | Path                        | Payload                                  | Status | Esperado | OK |
|--------|-----------------------------|------------------------------------------|--------|----------|----|
| GET    | /health                     | —                                        | 200    | 200      | ✓  |
| GET    | /                           | —                                        | 200    | 200      | ✓  |
| GET    | /tasks                      | —                                        | 200    | 200      | ✓  |
| GET    | /tasks/1                    | —                                        | 200    | 200      | ✓  |
| GET    | /tasks/search?q=bug         | —                                        | 200    | 200      | ✓  |
| GET    | /tasks/stats                | —                                        | 200    | 200      | ✓  |
| POST   | /tasks                      | {title,priority,user_id,category_id,...} | 201    | 201      | ✓  |
| PUT    | /tasks/12                   | {status,title}                           | 200    | 200      | ✓  |
| GET    | /users                      | —                                        | 200    | 200      | ✓  |
| GET    | /users/1                    | —                                        | 200    | 200      | ✓  |
| POST   | /users                      | {name,email,password,role}               | 201    | 201      | ✓  |
| PUT    | /users/5                    | {name,active}                            | 200    | 200      | ✓  |
| GET    | /users/1/tasks              | —                                        | 200    | 200      | ✓  |
| POST   | /login                      | {email,password}                         | 200    | 200      | ✓  |
| GET    | /reports/summary            | —                                        | 200    | 200      | ✓  |
| GET    | /reports/user/1             | —                                        | 200    | 200      | ✓  |
| GET    | /categories                 | —                                        | 200    | 200      | ✓  |
| POST   | /categories                 | {name,color}                             | 201    | 201      | ✓  |
| PUT    | /categories/6               | {name}                                   | 200    | 200      | ✓  |
| DELETE | /categories/6 (sem token)   | —                                        | 401    | 401      | ✓  |
| DELETE | /categories/6 (com token)   | Authorization: Bearer <token>            | 200    | 200      | ✓  |
| DELETE | /tasks/12 (com token)       | Authorization: Bearer <token>            | 200    | 200      | ✓  |
| DELETE | /users/5 (com token)        | Authorization: Bearer <token>            | 200    | 200      | ✓  |

## Amostras de resposta (trechos reais)
- GET /tasks/stats → 200 : {"cancelled":1,"completion_rate":10.0,"done":1,"in_progress":2,"overdue":2,"pending":6,"total":10}
- POST /tasks → 201 : {"id":11,"title":"Nova task de teste","status":"pending","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-31 00:00:00","tags":["a","b"], ...}
- POST /login → 200 : {"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxfQ.alVzGA.E_yz69pYvecVQNLjDa3fvNeKiJQ","user":{...SEM campo password...}}
- GET /users → 200 : [{"id":1,"name":"João Silva","email":"joao@email.com","role":"admin","active":true,"task_count":5}, ...]  (sem hash de senha)
- DELETE /categories/6 (sem token) → 401 : {"error":"Token ausente ou inválido"}

## Observações de contrato (mudanças intencionais de segurança)
- Campo `password` (hash) REMOVIDO de todas as respostas (era vazado em /users/<id>, /login, POST/PUT users).
- `/login` agora devolve token assinado (itsdangerous) no lugar do token de fachada 'fake-jwt-token-<id>'; o campo `token` (string) permanece.
- DELETE de /tasks, /users e /categories agora exige `Authorization: Bearer <token>` (401 sem token). Demais métodos e paths inalterados.

================================
RESULT: PASS (23/23 verificações — 22 endpoints + gate de auth)
================================
