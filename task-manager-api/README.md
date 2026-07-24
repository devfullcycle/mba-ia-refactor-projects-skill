# task-manager-api

API de Task Manager em Python/Flask + SQLAlchemy — tarefas com status, prioridade e prazo,
usuários, categorias e relatórios de produtividade.

Projeto refatorado para MVC pela skill [`refactor-arch`](.claude/skills/refactor-arch/).
Era o caso "parcialmente organizado": tinha `models/`, `routes/`, `services/` e `utils/`, mas
sem camada de controller — a regra de negócio vivia nas rotas e `services/`/`utils/` eram
código morto (19 símbolos definidos e nunca chamados).
Auditoria: [`reports/audit-project-3.md`](../reports/audit-project-3.md) ·
Validação: [`reports/validation-project-3.md`](../reports/validation-project-3.md).

## Como rodar

```bash
python3.9 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py     # popula 3 usuários, 4 categorias e 10 tasks
.venv/bin/python run.py
```

A aplicação sobe em `http://127.0.0.1:5000`. Rode o `seed.py` antes do primeiro boot, caso
contrário os endpoints retornam listas vazias.

Configuração por variáveis de ambiente — ver [`.env.example`](.env.example). Em
desenvolvimento a `SECRET_KEY` é efêmera (e os tokens emitidos deixam de valer a cada
restart); com `APP_ENV=production` a aplicação recusa iniciar sem ela. Sem `SMTP_*`
configurado, as notificações vão para o log em vez de tentar enviar e-mail.

## Estrutura

```
src/
├── config/{settings,logging_config}.py                 # ambiente → configuração
├── domain/constants.py                                 # status, papéis, limites, rótulos
├── models/{task,user,category}.py                      # entidade + invariantes + queries
├── validators/{task,user,category}_validator.py        # regra única de validação
├── services/{notification,token}_service.py            # notificação e token assinado
├── controllers/{task,user,category,report}_controller.py
├── views/{task,user,category,report,health}_routes.py  # só mapeamento
├── middlewares/{auth,error_handler}.py
├── utils/datetime_utils.py                             # now_utc (sem datetime.utcnow)
├── extensions.py                                       # instância do SQLAlchemy
└── app.py                                              # application factory
run.py · seed.py
```

## Endpoints

22 endpoints. Autenticação por token Bearer, obtido em `POST /login`:

| Grupo | Rotas | Autenticação |
|---|---|---|
| Tarefas | `GET|POST /tasks`, `GET /tasks/search`, `GET /tasks/stats`, `GET|PUT|DELETE /tasks/<id>` | pública |
| Usuários (leitura) | `GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks`, `POST /users` | pública |
| Usuários (escrita) | `PUT|DELETE /users/<id>` | token — o próprio usuário ou papel `admin` |
| Relatórios | `GET /reports/summary`, `GET /reports/user/<id>` | token |
| Categorias | `GET|POST /categories`, `PUT|DELETE /categories/<id>` | pública |
| Infra | `GET /`, `GET /health` | pública |

Senha mínima de 8 caracteres no cadastro via API (`PASSWORD_MIN_LENGTH`). As credenciais de
demonstração do `seed.py` (`joao@email.com` / `1234`, papel admin) são anteriores a essa regra
e continuam válidas para login.

## Validação

```bash
../scripts/smoke-project-3.sh /tmp/p3     # 42 chamadas nos 22 endpoints
```

As 7 chamadas às rotas protegidas retornam 401 nessa bateria — esperado sem token. Para
exercitá-las:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")

curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/reports/summary -H "Authorization: Bearer $TOKEN"
```
