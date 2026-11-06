# Validation Report — task-manager-api

> Gerado pela skill `refactor-arch` (Fase 4 — Validação Pós-Refatoração).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/task-manager-api`
> Baseado em: `reports/analysis-task-manager-api.md`, `reports/audit-task-manager-api.md`, `reports/refactor-task-manager-api.md`

## 1. Resumo

| Métrica | Resultado |
|---|---|
| Status geral | **PASS / VALIDATED** |
| Rotas de negócio testadas | 22/22 |
| Rotas aprovadas | 22 (100%) |
| CRITICAL resolvidos | **3/3** |
| HIGH resolvidos | **3/3** |
| Partial critical/high | **0** |
| Verificações estáticas | OK |
| Testes automatizados | 8/8 passed |
| Configuração usada | **padrão** (`AUTH_REQUIRED` ausente → `True`) |

**Status:** `VALIDATED`
**Recomendação:** `APROVADO`

## 2. Contrato original vs atual

Inventário extraído da Fase 1 (22 rotas de negócio; `/static` do Flask não conta).

| Recurso | Rotas no contrato original | Rotas hoje | Preservado |
|---|---|---|---|
| Aplicação | `GET /`, `GET /health` | 2 | ✅ |
| Tasks | `GET/POST /tasks`, `GET/PUT/DELETE /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats` | 7 | ✅ |
| Users | `GET/POST /users`, `GET/PUT/DELETE /users/<id>`, `GET /users/<id>/tasks` | 6 | ✅ |
| Auth | `POST /login` | 1 | ✅ |
| Reports | `GET /reports/summary`, `GET /reports/user/<id>` | 2 | ✅ |
| Categories | `GET/POST /categories`, `PUT/DELETE /categories/<id>` | 4 | ✅ |
| **Total** | **22** | **22** | **100%** |

Rotas registradas no Flask (`app.url_map`): 22 de negócio + `/static` = 23 regras.

**Mudanças de contrato intencionais e documentadas:** gestão de usuários passa a exigir `admin`; escritas exigem JWT por padrão; não-admin só opera nas próprias tarefas. Path, verbo e formato de resposta foram preservados.

## 3. Smoke test por endpoint

Servidor real com a configuração padrão: `DATABASE_URL=sqlite:////tmp/opencode/tm-etapa5.db PORT=5055 .venv/bin/python app.py`. Banco migrado e populado por `seed.py`.

| # | Método | Path | Esperado | Obtido | Resultado | Observação |
|---|---|---|---|---|---|---|
| 1 | GET | `/` | 200 | 200 | PASS | `{message, version}` |
| 2 | GET | `/health` | 200 | 200 | PASS | `{status, timestamp}` |
| 3 | GET | `/tasks` | 200 | 200 | PASS | inclui `user_name`, `category_name`, `overdue` |
| 4 | GET | `/tasks/search?q=login` | 200 | 200 | PASS | filtro aplicado |
| 5 | GET | `/tasks/stats` | 200 | 200 | PASS | 7 chaves preservadas |
| 6 | GET | `/tasks/1` | 200 | 200 | PASS | `to_dict` + `overdue` |
| 7 | POST | `/tasks` | 201 | 201 | PASS | dono derivado do JWT (usuário comum) |
| 8 | PUT | `/tasks/11` | 200 | 200 | PASS | atualização pelo dono |
| 9 | DELETE | `/tasks/11` | 200 | 200 | PASS | remoção pelo dono |
| 10 | GET | `/users` | 200 | 200 | PASS | listagem admin; **sem** `password` |
| 11 | GET | `/users/1` | 200 | 200 | PASS | usuário + `tasks` |
| 12 | GET | `/users/1/tasks` | 200 | 200 | PASS | campos originais + `overdue` |
| 13 | POST | `/users` | 201 | 201 | PASS | admin; **sem** `password` na resposta |
| 14 | PUT | `/users/4` | 200 | 200 | PASS | admin; nome atualizado |
| 15 | DELETE | `/users/4` | 200 | 200 | PASS | admin; `{message}` |
| 16 | POST | `/login` | 200 | 200 | PASS | JWT real (3 partes); público |
| 17 | GET | `/reports/summary` | 200 | 200 | PASS | 7 seções preservadas |
| 18 | GET | `/reports/user/1` | 200 | 200 | PASS | `user` + `statistics` |
| 19 | GET | `/categories` | 200 | 200 | PASS | `task_count` |
| 20 | POST | `/categories` | 201 | 201 | PASS | categoria criada (autenticado) |
| 21 | PUT | `/categories/5` | 200 | 200 | PASS | descrição atualizada |
| 22 | DELETE | `/categories/5` | 200 | 200 | PASS | `{message}` |

### Matriz de segurança (configuração padrão)

| Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|
| `POST /tasks` sem token | 401 | 401 | PASS |
| `POST /tasks` usuário comum | 201 | 201 | PASS |
| `POST /tasks` para outro usuário (não-admin) | 403 | 403 | PASS |
| `POST /users` sem token | 401 | 401 | PASS |
| `POST /users` não-admin | 403 | 403 | PASS |
| `POST /users` admin | 201 | 201 | PASS |
| `PUT /users/<id>` não-admin | 403 | 403 | PASS |
| `PUT /users/<id>` admin | 200 | 200 | PASS |
| `DELETE /users/<id>` não-admin | 403 | 403 | PASS |
| `DELETE /users/<id>` admin | 200 | 200 | PASS |
| `GET /users` sem token | 401 | 401 | PASS |
| `GET /users` não-admin | 403 | 403 | PASS |
| `GET /users` admin | 200 | 200 | PASS |
| `POST /login` | 200 | 200 | PASS |

### Comportamento de erro (regressão)

| Cenário | Antes | Agora | Resultado |
|---|---|---|---|
| `POST /tasks` com `{}` | 400 | 400 `Título é obrigatório` | PASS |
| `POST /tasks` com `priority: 9` | 400 | 400 | PASS |
| `POST /tasks` com `due_date` inválida | 400 | 400 | PASS |
| `POST /users` com e-mail inválido | 400 | 400 | PASS |
| `PUT /categories/<id>` com `null` | **500** (TypeError) | 400 `Dados inválidos` | PASS (melhoria) |
| `GET /tasks/99999` | 404 | 404 `Task não encontrada` | PASS |

**Nenhum erro 500 inesperado** durante o smoke test.

## 4. Verificação estática

| Item | Resultado | Evidência |
|---|---|---|
| Estrutura alvo presente | OK | `config/`, `controllers/`, `services/`, `repositories/`, `models/`, `routes/`, `middleware/`, `validators/`, `migrations/`, `tests/` |
| Rotas separadas do entrypoint | OK (WARN de baixo impacto) | 22 rotas de negócio em `routes/*.py`; `app.py` mantém `/` e `/health` inline (infraestrutura) |
| Controllers só orquestram | OK | `controllers/` sem `db`, models ou `.query`; handlers de 1-8 linhas |
| Services sem HTTP/request | OK | `services/` não usa `request`/`response`; `auth_service.py` usa `current_app` apenas para `SECRET_KEY`/expiração |
| Repositories sem HTTP | OK | `grep` não encontra Flask em `repositories/` |
| Queries parametrizadas | OK | ORM com parâmetros vinculados; sem SQL cru |
| Segredos hardcoded | OK | `grep` por `super-secret-key-123`, `senha123`, `smtp.gmail.com` → nenhuma ocorrência no código de produção |
| Arquivos órfãos | OK | `notification_service.py` removido; nenhum import remanescente; `import app` funciona |
| Config centralizada | OK | `config/settings.py` lê env; `.env.example` presente |
| **Auth default deny** | **OK** | `config/settings.py:31-34` default `True`; `middleware/auth.py:87-96` fail-closed (não consulta flag para desativar); `.env.example:15-17` `AUTH_REQUIRED=true` |
| **Autorização por papel** | **OK** | `middleware/auth.py:71-84` `require_role`; `controllers/user_controller.py:10-34` aplica `admin` em `GET/POST /users` e `PUT/DELETE /users/<id>`; `/login` sem decorator |
| **Identidade/posse do token** | **OK** | `middleware/auth.py:44-56` deriva `g.user_id`/`g.user_role` do `sub` e do cadastro autenticado; `services/task_service.py:108-127` resolve dono e bloqueia transferência para terceiro |
| **Hash em repouso** | **OK** | `models/user.py:31-41` usa `generate_password_hash`/`check_password_hash`; seed grava `scrypt:`; sem fallback de comparação em texto puro |
| APIs deprecated | OK | sem `datetime.utcnow()` nem `Query.get()` no código (só menção em docstring) |
| Error handling central | OK | `middleware/error_handler.py`; zero `except:` nu no projeto |
| Testes de segurança | OK | `tests/test_api.py` cobre 401, 403, 200/201, posse e `TestConfig.AUTH_REQUIRED=True` |

## 5. Cruzamento com auditoria (CRITICAL/HIGH)

### CRITICAL

| ID | Achado | Status | Evidência estática | Evidência dinâmica |
|---|---|---|---|---|
| SEC-02 | `SECRET_KEY` hardcoded (`app.py:13`) | **RESOLVIDO** | `config/settings.py:25` lê `SECRET_KEY` do ambiente; sem valor, `secrets.token_hex(32)`; nenhum literal no código de produção | Boot com config padrão sem `SECRET_KEY` → servidor sobe; `grep` sem `super-secret-key-123` |
| SEC-02 | Credenciais SMTP hardcoded | **RESOLVIDO** | `services/notification_service.py` removido; nenhum `smtp`/`senha123` no projeto | `grep` por `smtp.gmail.com` e `senha123` sem ocorrências |
| SEC-03 | MD5 + hash exposto | **RESOLVIDO** | `models/user.py:31-41` usa hashing seguro; `to_dict` (`:20-29`) não inclui `password`; login re-hasheia MD5 legado | Banco de seed: 3/3 senhas com prefixo `scrypt:` e nenhuma igual a `1234`/`abcd`/`pass`; login 200; `POST /users` e `/login` sem `password`; teste de re-hash passa |

### HIGH

| ID | Achado | Status | Evidência estática | Evidência dinâmica |
|---|---|---|---|---|
| SEC-04 | Rotas de escrita sem auth + token falso | **RESOLVIDO** | `middleware/auth.py:22-96` guard JWT central fail-closed com `g.user_id`/`g.user_role`; `controllers/user_controller.py:10-34` `@require_role('admin')`; `config/settings.py:34` default `True`; token fake eliminado | Config padrão: `POST /tasks` sem token 401; `POST /users` sem token 401; não-admin em `POST/PUT/DELETE /users` e `GET /users` → 403; admin → 201/200/200/200; `/login` 200 |
| ARCH-01 | Lógica de negócio nas rotas | **RESOLVIDO** | Regras em `services/task_service.py`, `user_service.py`, `category_service.py`, `report_service.py`; controllers com orquestração pura | Smoke test das 22 rotas e 8 testes de integração passando |
| ARCH-02 | Acesso a dados nas rotas | **RESOLVIDO** | Todo ORM em `repositories/` (3 arquivos); `grep` de `db`/`.query` em `controllers/` e `routes/` sem resultados | Boot e smoke test sem erros de persistência |

**Resumo:** CRITICAL **3/3** `RESOLVIDO`; HIGH **3/3** `RESOLVIDO`; `Partial critical/high: 0`.

## 6. Riscos e ressalvas (apenas MEDIUM/LOW)

1. **Rotas de leitura preservam o contrato original.** `GET /users/<id>` e `GET /users/<id>/tasks` continuam públicas. Não fazem parte do escopo do achado SEC-04 (escrita/autorização administrativa) e não expõem `password`. Avaliar restrição por dono/admin em iteração futura (LOW).
2. **`/` e `/health` inline em `app.py`:** rotas de infraestrutura; a separação das 22 rotas de negócio foi cumprida (LOW).
3. **`auth_service` usa `current_app`:** dependência do contexto de aplicação Flask, não de HTTP request/response (LOW).
4. **Migração de hashes MD5 legados:** o fallback existe apenas para re-hashear no login; não há comparação em texto puro. Recomenda-se forçar redefinição de senhas antigas (LOW).
5. **Baseline de banco legado:** bancos criados com o `create_all()` original precisam de `flask db stamp head` (LOW).
6. **Fora de escopo:** CI/CD, containerização, logging estruturado e testes unitários de services/repositories (LOW).

Nenhuma ressalva CRITICAL/HIGH.

## 7. Recomendação final

**APROVADO**

A refatoração preservou 100% das 22 rotas de negócio (path, verbo e formato), fechou **3/3 CRITICAL** e **3/3 HIGH**, incluindo SEC-04 com autenticação default deny, autorização `admin` e posse derivada do token. Não há pendências CRITICAL/HIGH (`Partial critical/high: 0`), falha funcional ou erro 500 inesperado.

## 8. Ações para retorno à Fase 3

**Nenhuma.** Todos os CRITICAL/HIGH estão `RESOLVIDO`; o gate bloqueante está satisfeito.

## 9. Notas e evidências

Comandos executados:

```bash
# Preparação e boot com configuração padrão (AUTH_REQUIRED não definido)
DATABASE_URL=sqlite:////tmp/opencode/tm-etapa5.db .venv/bin/python seed.py
DATABASE_URL=sqlite:////tmp/opencode/tm-etapa5.db PORT=5055 .venv/bin/python app.py

# Testes automatizados
.venv/bin/python -m pytest -q
# ........ [100%] 8 passed

# Config efetiva
.venv/bin/python -c "from config.settings import Config; print(Config.AUTH_REQUIRED)"
# True

# Senhas em repouso
# joao@email.com / maria@email.com / pedro@email.com → prefixo scrypt:
```

Smoke test HTTP: 22/22 PASS, 0 FAIL. Erros esperados: `{}` → 400, `null` → 400, id inexistente → 404. Matriz de segurança: 401/403/200-201 conforme a regra; `/login` público. Logs do servidor contêm apenas método, path e status — sem senha, token ou PII.

**Bloco de resumo:**

```
================================
PHASE 4: VALIDATION
================================
Project:               task-manager-api
Routes tested:         22/22
Routes passed:         22 (100%)
Critical resolved:     3/3
High resolved:         3/3
Partial critical/high: 0
Static checks:         OK
Status:                VALIDATED
Recommendation:        APROVADO
================================
```
