# Validation Report — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 4 — Validação Pós-Refatoração).
> Data: 2026-10-22 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/code-smells-project`
> Baseado em: `reports/analysis-code-smells-project.md`, `reports/audit-code-smells-project.md` e `reports/refactor-code-smells-project.md`

## 1. Resumo

| Campo | Resultado |
|---|---|
| Status geral | **PASS** (com ressalvas não bloqueantes) |
| Rotas do inventário testadas | **19/19** |
| Rotas aprovadas | **19/19 (100%)** |
| Rotas com contrato alterado (deliberado) | **7** (`POST /admin/query` removida; auth em `/admin/reset-db`; token no `/login`; auth de escrita em produtos/pedidos/status) |
| CRITICAL resolvidos | **3/3** |
| HIGH resolvidos | **4/4** |
| MEDIUM resolvidos | **4/5** (PERF-01 parcial) |
| LOW resolvidos | **3/4** (QUAL-06 não resolvido, por design) |
| Checks estáticos | **OK** (1 observação não bloqueante) |
| Smoke test automatizado | **68/68 passando** |
| Boot real (`python app.py`) | **OK** (porta 5111) |
| Recomendação | **APROVADO COM RESSALVAS** |

A refatoração preservou o contrato de sucesso de **todas** as 19 rotas
inventariadas na Fase 1 e corrigiu **todos** os achados CRITICAL e HIGH da
auditoria. As mudanças de contrato são deliberadas e exigidas pela auditoria:
`POST /admin/query` removida e rotas de escrita protegidas por token/nível
(SEC-04), com `POST /login` passando a emitir o token.

## 2. Contrato original vs atual

Contrato de referência: `reports/analysis-code-smells-project.md` §2.4 — 19 rotas,
entrypoint `app.py`, boot `python app.py` (porta 5000).

| # | Rota original (Fase 1) | Verbo/Path atual | Contrato de sucesso | Veredito |
|---|---|---|---|---|
| 1 | `GET /` | igual | `200 {"mensagem","versao","endpoints"}` preservado (`versao` agora de env, default `1.0.0`) | **PASS** |
| 2 | `GET /health` | igual | `200` com `status/database/counts`; campos `secret_key`/`db_path`/`debug` removidos | **PASS** (SEC-02) |
| 3 | `GET /produtos` | igual | `200 {"dados":[...],"sucesso":true}` | **PASS** |
| 4 | `GET /produtos/busca` | igual | `200 {"dados":[...],"total":N,"sucesso":true}` | **PASS** |
| 5 | `GET /produtos/<id>` | igual | `200 {"dados":{...},"sucesso":true}` / `404` | **PASS** |
| 6 | `POST /produtos` | **+ auth admin** | `201 {"dados":{"id":N},"mensagem":"Produto criado","sucesso":true}`; `401` sem token, `403` com nível `cliente` | **PASS** (SEC-04) |
| 7 | `PUT /produtos/<id>` | **+ auth admin** | `200 {"mensagem":"Produto atualizado","sucesso":true}` / `404`; `401` sem token | **PASS** (SEC-04) |
| 8 | `DELETE /produtos/<id>` | **+ auth admin** | `200 {"mensagem":"Produto deletado","sucesso":true}` / `404`; `401` sem token | **PASS** (SEC-04) |
| 9 | `GET /usuarios` | igual | `200 {"dados":[...],"sucesso":true}`; campo `senha` removido | **PASS** (SEC-03) |
| 10 | `GET /usuarios/<id>` | igual | `200` / `404`; campo `senha` removido | **PASS** (SEC-03) |
| 11 | `POST /usuarios` | igual | `201 {"dados":{"id":N},"sucesso":true}` | **PASS** |
| 12 | `POST /login` | **+ token** | `200 {"dados":{...},"token":"...","mensagem":"Login OK","sucesso":true}` / `401` | **PASS** (SEC-04) |
| 13 | `POST /pedidos` | **+ auth cliente** | `201 {"dados":{"pedido_id":N,"total":V},"mensagem":...,"sucesso":true}` / `400`; `401` sem token, `403` para admin/outro usuário | **PASS** (SEC-04) |
| 14 | `GET /pedidos` | igual | `200 {"dados":[...com itens...],"sucesso":true}` | **PASS** |
| 15 | `GET /pedidos/usuario/<id>` | igual | `200 {"dados":[...com itens...],"sucesso":true}` | **PASS** |
| 16 | `PUT /pedidos/<id>/status` | **+ auth admin** | `200 {"mensagem":"Status atualizado","sucesso":true}` / `400`; `401` sem token | **PASS** (SEC-04) |
| 17 | `GET /relatorios/vendas` | igual | `200 {"dados":{agregados},"sucesso":true}` | **PASS** |
| 18 | `POST /admin/reset-db` | **+ auth** | `200 {"mensagem":"Banco de dados resetado","sucesso":true}`; agora exige `Bearer` (`401` sem token) | **PASS** (mudança por SEC-04) |
| 19 | `POST /admin/query` | **removida** | `404` | **PASS** (remoção deliberada, SEC-01/SEC-04) |

**Stack/entrypoint:** inalterados — Python 3.12 + Flask 3.1.1 + Flask-CORS 5.0.1 + SQLite (`sqlite3`).
Entrypoint continua `app.py`; boot continua `python app.py`; banco continua `loja.db` por default
(agora configurável por `DATABASE_PATH`).

**Formatos de erro:** unificados em `{"erro": ..., "sucesso": false}` pelo handler central
(antes eram `{"erro": ...}` sem `sucesso`, exceto em alguns pontos).

## 3. Smoke test por endpoint

Ambiente: `SECRET_KEY=val-secret ADMIN_TOKEN=val-admin-token DATABASE_PATH=... PORT=5111 python app.py`.
Rotas exercitadas via `curl` contra o servidor real.

| # | Método | Path | Status | Resultado | Observação |
|---|---|---|---|---|---|
| 1 | GET | `/health` | 200 | **PASS** | `counts {produtos:10,usuarios:3,pedidos:0}`; sem `secret_key`/`db_path`/`debug` |
| 2 | GET | `/` | 200 | **PASS** | 6 recursos listados |
| 3 | GET | `/produtos` | 200 | **PASS** | 10 itens do seed |
| 4 | GET | `/produtos/busca?q=Mouse` | 200 | **PASS** | `total:1` |
| 5 | GET | `/produtos/busca?q=' OR '1'='1` | 200 | **PASS** | `total:0` — **SQLi neutralizada** (antes retornava toda a tabela) |
| 6 | GET | `/produtos/1` | 200 | **PASS** | Notebook Gamer 5999.99 |
| 7 | GET | `/produtos/9999` | 404 | **PASS** | `Produto não encontrado` |
| 8 | POST | `/produtos` (sem token) | 401 | **PASS** | `Token de acesso ausente` — SEC-04 |
| 8b | POST | `/produtos` (token cliente) | 403 | **PASS** | `Perfil sem permissão` — SEC-04 |
| 8c | POST | `/produtos` (token admin) | 201 | **PASS** | `{"dados":{"id":11}}` |
| 9 | POST | `/produtos` (`preco:"abc"`, admin) | 400 | **PASS** | `preco deve ser numérico` (antes podia virar 500) |
| 10 | PUT | `/produtos/11` (admin) | 200 | **PASS** | atualização aplicada |
| 11 | DELETE | `/produtos/11` (admin) | 200 | **PASS** | `Produto deletado` |
| 12 | GET | `/usuarios` | 200 | **PASS** | 3 usuários **sem campo `senha`** |
| 13 | GET | `/usuarios/1` | 200 | **PASS** | `admin@loja.com`, sem `senha` |
| 14 | POST | `/usuarios` | 201 | **PASS** | `{"dados":{"id":4}}` |
| 15 | POST | `/login` | 200 | **PASS** | `Login OK`; devolve `token` de sessão, sem `senha` |
| 16 | POST | `/pedidos` (token cliente) | 201 | **PASS** | `total:479.7`; estoque debitado |
| 16b | POST | `/pedidos` (sem token) | 401 | **PASS** | `Token de acesso ausente` — SEC-04 |
| 16c | POST | `/pedidos` (token admin) | 403 | **PASS** | `Perfil sem permissão` — SEC-04 |
| 16d | POST | `/pedidos` (outro `usuario_id`) | 403 | **PASS** | `Cliente só pode criar pedido para si mesmo` |
| 17 | GET | `/pedidos` | 200 | **PASS** | 1 pedido com itens e `produto_nome` |
| 18 | GET | `/pedidos/usuario/2` | 200 | **PASS** | 1 pedido com itens |
| 19 | PUT | `/pedidos/1/status` (admin) | 200 | **PASS** | `Status atualizado` |
| 19b | PUT | `/pedidos/1/status` (sem token) | 401 | **PASS** | `Token de acesso ausente` — SEC-04 |
| 20 | GET | `/relatorios/vendas` | 200 | **PASS** | agregados e desconto corretos |
| 21 | POST | `/admin/query` | 404 | **PASS** | endpoint removido |
| 22 | POST | `/admin/reset-db` (sem token) | 401 | **PASS** | `Token administrativo ausente` |
| 23 | POST | `/admin/reset-db` (com token) | 200 | **PASS** | base limpa |

**Boot:** `python app.py` subiu sem erros; log confirma `Debug mode: off` e servidor em `http://127.0.0.1:5111`.

**Suíte automatizada `tests/smoke_contract.py`:** **68/68 checks** passando, incluindo
verificações de segurança (SQLi, bypass de login, hash de senha, rollback de estoque,
autorização por nível `admin`/`cliente` e posse do pedido).

## 4. Verificação estática

| Check | Resultado | Evidência |
|---|---|---|
| Estrutura alvo presente | **OK** | `routes/`, `controllers/`, `schemas/`, `services/`, `repositories/`, `models/`, `database/`, `middleware/`, `config.py`, `errors.py` |
| Rotas separadas do entrypoint | **OK** | `routes/*.py` (Blueprints); `app.py:34` chama `routes.init_app(app)` |
| Controllers só orquestram | **OK** | `controllers/__init__.py` — sem SQL, sem `for`/cálculo; chama `schemas` + `services` |
| Services com regra de negócio | **OK** | `services/pedido_service.py` (total, desconto, status), `services/usuario_service.py` (auth) |
| Repositories com acesso a dados | **OK** | `repositories/*.py`; só eles importam `get_db` para queries |
| Queries parametrizadas | **OK** | 8 ocorrências de interpolação são **constantes** (nomes de coluna/tabela fixos); todo valor de usuário usa `?` |
| Sem segredos hardcoded | **OK** | grep por `secret/password/token/api_key = "<literal>"` → nenhum; `SECRET_KEY` via env (`config.py:16`) |
| Arquivos órfãos removidos | **OK** | `controllers.py`, `models.py`, `database.py` deletados; imports remanescentes apontam para os **pacotes novos** |
| Config via ambiente | **OK** | `config.py` + `.env.example`; defaults seguros para não-sensíveis |
| `git status` sem sobras | **OK** | sem `__pycache__`/`loja.db` de execução |

### Observações estáticas não bloqueantes

- **`GET /health` não valida disponibilidade do banco no boot:** o handler conta registros
  via repositories; se o banco estivesse indisponível, o handler central devolveria 500 em vez
  de um `status: "erro"`. O código original também retornava 500 nesse caso — **sem regressão**.
- **`POST /produtos` valida faixas de negócio (nome, categoria, preço, estoque) via `models.Produto`**
  chamado pelo service. Isso é coerente com o Padrão 5 (validação de negócio no service), embora
  parte da checagem de faixa de `preço`/`estoque` pareça "schema". Não bloqueia.

## 5. Cruzamento com auditoria (CRITICAL/HIGH)

| ID | Severidade | Classificação | Evidência da resolução |
|---|---|---|---|
| **SEC-01** SQL Injection | CRITICAL | **RESOLVIDO** | `repositories/*.py` usam `?`; grep confirma que nenhuma interpolação carrega entrada de usuário; smoke: `?q=' OR '1'='1` → `total:0` e `POST /login` com injeção → `401`. `/admin/query` (SQL arbitrário) removida → `404`. |
| **SEC-02** Credencial hardcoded | CRITICAL | **RESOLVIDO** | `SECRET_KEY` lida de env em `config.py:16`; nenhum literal no código; `services/health_service.py` não devolve `secret_key`/`db_path`/`debug` (validado: `/health` só traz 5 campos). |
| **SEC-03** Senhas em texto plano | CRITICAL | **RESOLVIDO** | `services/usuario_service.py` usa `generate_password_hash`/`check_password_hash`; senha gravada como `scrypt:32768:8:...`; `senha` ausente em `GET /usuarios` e `GET /usuarios/<id>`; login legado re-hasheia no sucesso. |
| **SEC-04** Rotas sem auth | HIGH | **RESOLVIDO (escrita)** | `POST /admin/reset-db` protegida por `require_admin` (token estático). `/login` emite token de sessão assinado (`services/auth_service.py`); `require_tipos` protege escrita: produtos (`POST`/`PUT`/`DELETE`) e status de pedido exigem `admin`; `POST /pedidos` exige `cliente` e só aceita o próprio `usuario_id`. `401` sem token, `403` com nível insuficiente. *Ressalva:* rotas `GET` de negócio continuam públicas para preservar contrato. |
| **ARCH-01** Lógica no Controller | HIGH | **RESOLVIDO** | `controllers/__init__.py` — handlers de 3-6 linhas, sem `for`/cálculo/regra; regras em `services/produto_service.py`, `pedido_service.py`, `usuario_service.py`. |
| **ARCH-02** Dados no Controller | HIGH | **RESOLVIDO** | Nenhum `execute`/`get_db` em `controllers/` ou `app.py`; SQL concentrado em `repositories/` e `services/admin_service.py`. |
| **QUAL-02** Validação ausente/frágil | HIGH | **RESOLVIDO** | `schemas/validators.py` valida presença, tipo e `get_json(silent=True)`; smoke valida 400 para body ausente, tipo textual, faixa e obrigatoriedade. |

**Resultado: 7/7 CRITICAL+HIGH resolvidos.**

### MEDIUM/LOW (não bloqueiam)

| ID | Severidade | Classificação | Observação |
|---|---|---|---|
| ARCH-03 Model duplo | MEDIUM | **RESOLVIDO** | `models.py` eliminado; papéis separados. |
| QUAL-01 God File | MEDIUM | **RESOLVIDO** | maior arquivo 139 LOC (antes 314). |
| QUAL-02b Estoque não atômico | MEDIUM | **RESOLVIDO** | `UPDATE ... WHERE estoque >= ?` + `BEGIN IMMEDIATE` + rollback; smoke confirma que pedido rejeitado não debita estoque. |
| QUAL-03 Erro genérico | MEDIUM | **RESOLVIDO** | `middleware/error_handler.py` central; `500` genérico + `logger.exception`. |
| QUAL-04 Estado global mutável | MEDIUM | **RESOLVIDO** | `database/connection.py` usa `flask.g` por request + teardown. |
| PERF-01 N+1 | MEDIUM | **PARCIAL** | Listagens usam JOIN único; gravação de pedido reusa a linha da validação (sem reconsulta). Resta 1 query por item na validação de estoque — reduzido, sem impacto de contrato. |
| SEC-06 Log sensível | LOW | **RESOLVIDO** | `services/notificacao_service.py` usa `logging` sem PII. |
| QUAL-05 Imports mortos | LOW | **RESOLVIDO** | imports mortos removidos; `SECRET_KEY` agora usada. |
| QUAL-07 Config hardcoded | LOW | **RESOLVIDO** | `config.py` + `.env.example`. |
| QUAL-08 Sem testes | LOW | **RESOLVIDO** | `tests/smoke_contract.py` (68 checks). |
| QUAL-06 Sem migrations | LOW | **NÃO RESOLVIDO (por design)** | Schema segue inline em `database/schema.py` para preservar o boot; recomendado Alembic + constraints. |

## 6. Riscos e ressalvas

- **Autenticação parcial:** rotas de escrita estão protegidas por nível (`admin`/`cliente`),
  mas as rotas `GET` de usuários, pedidos e relatórios continuam públicas para preservar o
  contrato original. Risco residual de exposição de leitura (SEC-04).
- **Token sem revogação:** token é stateless e vale por `TOKEN_MAX_AGE_SECONDS` (padrão 8h);
  não há logout/revogação individual.
- **PERF-01 residual:** validação de itens em `POST /pedidos` faz 1 query por item.
- **QUAL-06:** sem migrations e sem `UNIQUE(email)`/`CHECK`/`FOREIGN KEY`.
- **Migração de senhas legadas:** o caminho de login ainda aceita comparação em texto puro
  para registros antigos (com upgrade imediato). Recomenda-se re-hash em lote.
- **Testes:** cobre contrato e segurança; não há teste unitário de services/repositories.
- **Sem CI/CD:** o smoke test não está em pipeline.

## 7. Recomendação final

**APROVADO COM RESSALVAS**

A Fase 3 preservou o contrato de sucesso das 19 rotas do inventário, corrigiu
7/7 achados CRITICAL+HIGH e não introduziu regressões (68/68 smoke checks; boot real validado).
As ressalvas são melhorias incrementais, não bloqueios:

1. Proteger também as rotas `GET` de usuários/pedidos/relatórios e adicionar revogação de token (SEC-04 residual).
2. Completar PERF-01 com `IN (...)` único na validação de itens.
3. Adotar migrations (Alembic) + constraints de integridade (QUAL-06).
4. Re-hash em lote das senhas legadas e remover o fallback de texto puro.
5. Adicionar testes unitários de services/repositories e um pipeline de CI.

**Nenhuma ação corretiva é exigida antes de considerar o fluxo concluído.**

## 8. Notas e evidências

- **Comandos executados:**
  - Boot: `SECRET_KEY=val-secret ADMIN_TOKEN=val-admin-token DATABASE_PATH=/tmp/opencode/val.db PORT=5111 python app.py`
  - Smoke: `python tests/smoke_contract.py` → `68/68 checks passaram`
  - Estática: `grep -rnE "execute\(.*(\+|%|\.format\(|f['\"])" --include='*.py' .`
  - Segredos: `grep -rniE "(secret|password|token|api_key)\s*=\s*['\"][^'\"]{6,}" --include='*.py' .`
- **Contrato de referência:** `reports/analysis-code-smells-project.md` §2.4 (19 rotas).
- **Achados de referência:** `reports/audit-code-smells-project.md` §2.
- **Venv:** execuções em `/tmp/opencode/refactor-venv` (Flask 3.1.1). `requirements.txt` não foi alterado.
- **Limpeza:** `__pycache__` e `loja.db` de execução removidos; `git status` sem sobras.
- **Fase 4 original:** nenhum arquivo de código-fonte foi modificado (somente verificação + relatório).

## 9. Atualização — autorização por nível (SEC-04)

A validação original registrava SEC-04 como resolvido apenas no escopo
administrativo. A atualização posterior implementou autenticação de sessão e
autorização por nível nas rotas de escrita:

| Rota | Nível | Implementação |
|---|---|---|
| `POST /login` | público | emite `token` assinado com `SECRET_KEY` (`services/auth_service.py`) |
| `POST`/`PUT`/`DELETE /produtos` | `admin` | `require_tipos(Config.PERFIL_ADMIN)` em `routes/produto_routes.py` |
| `POST /pedidos` | `cliente` | `require_tipos(Config.PERFIL_CLIENTE)` + validação de posse no controller |
| `PUT /pedidos/<id>/status` | `admin` | `require_tipos(Config.PERFIL_ADMIN)` em `routes/pedido_routes.py` |

O guard relê o usuário no banco a cada requisição, portanto o nível nunca vem
do corpo do token. `401` indica token ausente/inválido/expirado; `403` indica
usuário autenticado sem o nível exigido (ou tentando criar pedido para outro
usuário). Seed exercitado: `admin@loja.com`/`admin123` e
`joao@email.com`/`123456`.

**Evidência:** `python tests/smoke_contract.py` → **68/68 checks**, incluindo
os cenários `401`/`403`/`201` de produtos e pedidos.

**Arquivos alterados nesta atualização:** `middleware/auth.py`,
`services/auth_service.py`, `controllers/__init__.py`, `routes/produto_routes.py`,
`routes/pedido_routes.py`, `config.py`, `.env.example`, `tests/smoke_contract.py`.
