# Validação — Projeto 3 (task-manager-api)

Protocolo de `references/validation.md`: baseline capturado antes de qualquer modificação,
refatoração aplicada, mesma bateria reexecutada e comparada.

- Runtime: Python 3.9.5 (venv local), Flask 3.0.0, SQLAlchemy 2.0.51
- Antes: `python app.py` — Após: `python run.py` (seed por `python seed.py`)
- Banco recriado do zero e semeado com os mesmos dados nas duas execuções
- Bateria: 42 chamadas cobrindo os 22 endpoints, mais 16 checagens de autenticação/autorização

## Resultado

```
Validation
  ✓ Application boots without errors        (log limpo, "Debug mode: off")
  ✓ 33/33 chamadas de endpoints não protegidos com status idêntico ao baseline
  ✓ 9/9 diferenças são intencionais (autenticação nas rotas sensíveis + política de senha)
  ✓ Payload idêntico ao baseline em 15 de 16 endpoints comparados
    (a exceção é a remoção do hash de senha — finding 2)
  ✓ Relatórios com token: mesmas chaves e mesma estrutura do baseline
  ✓ No hardcoded secrets remaining          (grep vazio em src/, run.py, seed.py)
  ✓ Zero APIs deprecated: nenhum utcnow(), nenhum Query.get(), nenhum Model.query
  ✓ Nenhum DeprecationWarning/LegacyAPIWarning ao importar a aplicação
  ✓ Layer boundaries respected              (ORM só em models/, sem HTTP em models/services)
  ✓ Camada fantasma eliminada: NotificationService, TokenService, is_overdue e os
    validadores agora têm uso real (antes: só a definição)
  ✓ import de src.app não executa create_all
```

## Comparação status a status

Endpoints sem mudança de contrato (33 chamadas, todas idênticas):

| Grupo | Chamadas | Baseline = Após |
|---|---|---|
| `/` e `/health` | 2 | ✓ |
| `/tasks` (list, get, 404, search ×2, stats) | 6 | ✓ |
| `/tasks` escrita (create, 3× 400, 404 relação, update, 404, delete, 404) | 9 | ✓ |
| `/users` leitura (list, get, 404, tasks) | 4 | ✓ |
| `/users` validação (400 email, 400 vazio) | 2 | ✓ |
| `/login` (ok, 401, 400) | 3 | ✓ |
| `/categories` (list, create, 400, update, 404, delete, 404) | 7 | ✓ |

Endpoints com mudança intencional (9 chamadas):

| Chamada | Baseline | Após (sem token) | Após (com token) | Finding |
|---|---|---|---|---|
| GET /reports/summary | 200 | 401 | 200 | 7 |
| GET /reports/user/1 | 200 | 401 | 200 | 7 |
| GET /reports/user/999999 | 404 | 401 | 404 | 7 |
| PUT /users/4 | 200 | 401 | 200 | 7 |
| PUT /users/999999 | 404 | 401 | 404 | 7 |
| DELETE /users/4 | 200 | 401 | 200 | 7 |
| DELETE /users/999999 | 404 | 401 | 404 | 7 |
| POST /users (senha de 5 caracteres) | 201 | 400 | — | 19 |
| POST /users (e-mail duplicado, senha de 5 caracteres) | 409 | 400 | 409 com senha válida | 19 |

Todas as 9 voltam ao comportamento do baseline quando a chamada atende às novas regras
(token válido e senha de ≥8 caracteres) — nenhuma funcionalidade foi perdida.

## Checagens de autenticação e autorização

| Checagem | Resultado |
|---|---|
| `POST /login` devolve token assinado (`itsdangerous`) | ✓ `eyJzdWIiOjEsInJvbGUiOiJhZG1pbiJ9.…` |
| Token inválido em rota protegida | 401 ✓ |
| Token ausente em rota protegida | 401 ✓ |
| Usuário comum altera a própria conta | 200 ✓ |
| Usuário comum altera conta de outro | **403** ✓ |
| Usuário comum deleta conta de outro | **403** ✓ |
| Admin altera conta de outro | 200 ✓ |
| `POST /users` com senha ≥8 caracteres | 201 ✓ |
| `POST /users` com e-mail duplicado e senha válida | 409 ✓ |

## Diferenças intencionais de contrato

| Mudança | Antes | Depois | Finding |
|---|---|---|---|
| Hash de senha na resposta | `to_dict()` incluía `"password": "81dc9bdb52d04dc20036dbd8313ed055"` (MD5 de `1234`) em `GET /users/<id>`, `POST /users` e `POST /login` | campo removido da serialização | 2 |
| Algoritmo de hash | MD5 sem salt | scrypt com salt por usuário (`werkzeug.security`) | 1 |
| Token de sessão | `'fake-jwt-token-' + id` (previsível, nunca verificado) | token assinado com `SECRET_KEY` e TTL configurável | 7 |
| Relatórios e escrita de conta | abertos | exigem token; conta alheia exige papel admin | 7 |
| Mínimo de senha | 4 caracteres | 8 (configurável por `PASSWORD_MIN_LENGTH`) | 19 |
| `priority` não numérico no PUT | `TypeError` → 500 | 400 com mensagem de validação | 11 |
| Cor de categoria inválida | aceita silenciosamente | 400 (`#RRGGBB`) | — (regra que existia em `helpers.is_valid_color`, nunca usada) |
| Envelope de erro | `{'error': ...}` | mantido `{'error': ...}` | — |

## Evidência das correções

### Hash de senha vazado (findings 1 e 2)

```console
# ANTES — POST /login
{"message":"Login realizado com sucesso",
 "user":{"active":true,"created_at":"...","email":"joao@email.com","id":1,"name":"João Silva",
         "password":"81dc9bdb52d04dc20036dbd8313ed055","role":"admin"},
 "token":"fake-jwt-token-1"}

# DEPOIS — sem hash, com token assinado
{"message":"Login realizado com sucesso",
 "user":{"active":true,"created_at":"...","email":"joao@email.com","id":1,"name":"João Silva",
         "role":"admin"},
 "token":"eyJzdWIiOjEsInJvbGUiOiJhZG1pbiJ9.amPcFA..."}
```

`81dc9bdb52d04dc20036dbd8313ed055` é o MD5 de `1234` — reversível por consulta pública.

### APIs deprecated (findings 15 e 16)

```console
# ANTES — em runtime, com SQLAlchemy 2.0.51
LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of
SQLAlchemy and becomes a legacy construct in 2.0. (deprecated since: 2.0)

# DEPOIS
$ grep -rn "utcnow()\|\.query\.get(\|\.query\.filter\|\.query\.all(" src/ run.py seed.py
(nenhuma ocorrência em código)

$ python -c "import warnings; warnings.simplefilter('always'); import src.app"
(nenhum DeprecationWarning ou LegacyAPIWarning)
```

Sobre a escolha de fuso: `datetime.utcnow()` foi trocada por `now_utc()`
(`src/utils/datetime_utils.py`), que devolve `datetime.now(timezone.utc).replace(tzinfo=None)`.
Manter UTC *naive* preserva a semântica das colunas `DateTime` do SQLite e o formato das
respostas; migrar para datetimes *aware* exigiria `DateTime(timezone=True)` e mudaria o
payload — é uma mudança separada, registrada como recomendação.

### Camada fantasma (finding 5)

| Símbolo | Antes | Depois |
|---|---|---|
| `NotificationService` | 1 ocorrência (definição) | 4 — usado pelo `TaskController` na atribuição de tarefa |
| `Task.is_overdue()` | 1 ocorrência (definição) | 4 — única definição de "atrasada", usada por `to_dict` e pelos relatórios |
| `VALID_STATUSES` | 1 ocorrência | 4 — usada pelos validadores e pelo model |
| `process_task_data` / `helpers` órfãos | definidos e nunca chamados | substituídos por `src/validators/` com uso real |
| `marshmallow`, `requests`, `python-dotenv` | declarados no requirements, nunca importados | removidos do requirements |

### N+1 (finding 8)

| Endpoint | Antes | Depois |
|---|---|---|
| `GET /tasks` | 1 + 2N queries (`User.query.get` e `Category.query.get` por tarefa) | 1 query com `joinedload` |
| `GET /users` | 1 + N (`len(u.tasks)` por usuário) | 1 query com `outerjoin` + `group_by` |
| `GET /reports/summary` | 15 queries + 1 por usuário | agregações em SQL (`group_by`, `case`) |
| `GET /categories` | 1 + N (`count()` por categoria) | 1 query com `outerjoin` + `group_by` |

## Checagens estruturais

| Checagem | Resultado |
|---|---|
| Segredo literal | vazio ✓ |
| `datetime.utcnow()` em código | vazio ✓ |
| Legacy Query API (`.query.get/filter/all/count`) | vazio ✓ |
| `except:` nu | vazio ✓ |
| `print()` em `src/` | vazio ✓ |
| `type(x) == …` | vazio ✓ |
| ORM/`select()` fora de `src/models/` | vazio ✓ |
| `flask`/`jsonify`/`request` em `models/` ou `services/` | vazio ✓ |
| `create_all()` no import | não ocorre ✓ |

## Estrutura antes e depois

| | Antes | Depois |
|---|---|---|
| Arquivos `.py` | 15 | 37 |
| Linhas | 1.158 | 1.880 |
| Maior arquivo | `routes/task_routes.py` (299 linhas) | `src/models/task.py` (272 linhas) |
| Maior função | `summary_report` (90 linhas) | `ReportController.summary` (44 linhas, sem regra de negócio) |
| Camadas | models, routes, services (morto), utils (morto) | config, domain, models, validators, services, controllers, views, middlewares, utils |

O aumento de linhas vem da separação de camadas, dos validadores e da documentação dos
módulos — as três rotas que somavam 733 linhas passaram a 4 controllers (≈390 linhas) mais
5 blueprints de mapeamento puro (≈150 linhas).

## Log de boot após a refatoração

```
2026-07-24 18:41:24,198 WARNING  [src.app] SECRET_KEY não definida no ambiente — usando chave
                                 efêmera de desenvolvimento. Os tokens emitidos deixam de valer
                                 a cada restart.
2026-07-24 18:41:24,208 INFO     [src.services.notification_service] SMTP não configurado —
                                 notificações serão registradas no log
2026-07-24 18:41:24,213 INFO     [src.app] Servidor iniciado em http://127.0.0.1:5000 (development)
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

## Riscos residuais (registrados por honestidade)

1. **CRUD de tarefas e categorias segue sem autenticação.** Protegi o que expõe ou altera
   dados de terceiros (relatórios agregados e contas de usuário). Exigir token no CRUD de
   tarefas mudaria o contrato de 11 endpoints e é decisão de produto, não de refatoração.
2. **`GET /users` continua listando nome e e-mail sem autenticação.** Mesma razão acima; o
   middleware está pronto e aplicá-lo é uma linha por rota.
3. **Senhas de demonstração no seed** (`1234`, `abcd`, `pass`) ficam abaixo do novo mínimo de
   8 caracteres, que vale para o cadastro via API. Em um sistema real, a mudança de política
   exigiria redefinição de senha dos usuários existentes.
4. **Datas seguem UTC naive** por compatibilidade de payload e de comparação — ver nota acima.
