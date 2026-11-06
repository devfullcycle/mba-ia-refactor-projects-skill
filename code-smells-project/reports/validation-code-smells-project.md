# Validation Report — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 4 — Validação Pós-Refatoração).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/code-smells-project`
> Baseado em: `reports/analysis-code-smells-project.md`, `reports/audit-code-smells-project.md` e `reports/refactor-code-smells-project.md`
> Reexecução da Etapa 6: valida o fechamento de SEC-03 em repouso (seed com hash, migração de legado no boot e login sem comparação em texto puro).

## 1. Resumo

| Campo | Resultado |
|---|---|
| Status geral | **PASS** |
| Rotas do inventário testadas | **19/19** |
| Rotas aprovadas | **19/19 (100%)** |
| Rotas com contrato alterado (deliberado) | **7** (`POST /admin/query` removida; auth em `/admin/reset-db`; token no `/login`; auth de escrita em produtos/pedidos/status) |
| CRITICAL resolvidos | **3/3** |
| HIGH resolvidos | **4/4** |
| CRITICAL pendentes | **0** |
| HIGH pendentes | **0** |
| Partial critical/high | **0** |
| MEDIUM resolvidos | **4/5** (PERF-01 com resíduo documentado, não bloqueante) |
| LOW resolvidos | **3/4** (QUAL-06 fora de escopo por design) |
| Checks estáticos | **OK** |
| Smoke test automatizado | **73/73 passando** |
| Boot real (`python app.py`) | **OK** (portas 5066 e 5067) |
| Recomendação | **APROVADO** |

**Gate da Etapa 6:**

- `Critical resolved: 3/3`
- `High resolved: 4/4`
- `Partial critical/high: 0`
- `SEC-03: RESOLVIDO`
- `Smoke test: 73/73`

A refatoração preservou o contrato de sucesso de **todas** as 19 rotas
inventariadas na Fase 1 e corrigiu **todos** os achados CRITICAL e HIGH da
auditoria. As mudanças de contrato são deliberadas e exigidas pela auditoria:
`POST /admin/query` removida e rotas de escrita protegidas por token/nível
(SEC-04), com `POST /login` emitindo token de sessão.

Nesta reexecução, SEC-03 foi validado também **em repouso**: o banco novo não
contém nenhuma senha em texto puro, o login usa exclusivamente
`check_password_hash` e registros legados são re-hasheados no boot antes de
qualquer autenticação.

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
| 11 | `POST /usuarios` | igual | `201 {"dados":{"id":N},"sucesso":true}`; senha persistida com hash | **PASS** (SEC-03) |
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

**Formatos de erro:** unificados em `{"erro": ..., "sucesso": false}` pelo handler central.

## 3. Smoke test por endpoint e matriz manual

Ambiente principal: `SECRET_KEY=etapa6-secret ADMIN_TOKEN=etapa6-admin-token DATABASE_PATH=/tmp/opencode/cs-etapa6.db PORT=5066 python app.py`.
Rotas exercitadas contra o servidor real; suíte automatizada executada em paralelo.

| # | Método | Path | Status | Resultado | Observação |
|---|---|---|---|---|---|
| 1 | GET | `/health` | 200 | **PASS** | `counts {produtos:10,usuarios:3,pedidos:0}`; sem `secret_key`/`db_path`/`debug` |
| 2 | GET | `/` | 200 | **PASS** | 6 recursos listados |
| 3 | GET | `/produtos` | 200 | **PASS** | 10 itens do seed |
| 4 | GET | `/produtos/busca?q=Mouse` | 200 | **PASS** | `total:1` |
| 5 | GET | `/produtos/busca?q=' OR '1'='1` | 200 | **PASS** | `total:0` — **SQLi neutralizada** |
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
| 14 | POST | `/usuarios` | 201 | **PASS** | `{"dados":{"id":4}}`; senha persistida como `scrypt:` |
| 15 | POST | `/login` (admin) | 200 | **PASS** | `Login OK`; devolve `token` de sessão, sem `senha` |
| 15b | POST | `/login` (joao) | 200 | **PASS** | seed com hash autentica |
| 15c | POST | `/login` (maria) | 200 | **PASS** | seed com hash autentica |
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

**Boot:** `python app.py` subiu sem erros; log confirma `Debug mode: off` e servidor em `http://127.0.0.1:5066`.

**Suíte automatizada `tests/smoke_contract.py`:** **73/73 checks** passando, incluindo
verificações de segurança (SQLi, bypass de login, hash de senha, rollback de estoque,
autorização por nível `admin`/`cliente`, posse do pedido, seed em repouso, ausência de
texto puro e migração de legado).

## 4. SEC-03 — validação em repouso e migração

### 4.1 Banco novo (seed)

Banco criado do zero em `/tmp/opencode/cs-etapa6.db` e inspecionado via `sqlite3`:

| E-mail | Valor armazenado | Prefixo | Comprimento | Texto puro? |
|---|---|---|---|---|
| `admin@loja.com` | hash scrypt | `scrypt:32768` | 162 | não |
| `joao@email.com` | hash scrypt | `scrypt:32768` | 162 | não |
| `maria@email.com` | hash scrypt | `scrypt:32768` | 162 | não |

- Nenhum valor é igual a `admin123`, `123456` ou `senha123`.
- Login dos três usuários do seed retornou `200`, com token e sem `senha` no corpo.

### 4.2 Login sem comparação em texto puro

- `services/usuario_service.py:autenticar` só aceita valores que começam com
  `pbkdf2:`/`scrypt:`/`argon2` e delega a verificação a `check_password_hash`.
- Não existe mais `stored == senha_informada`, nem fallback de re-hash no login.
- O smoke test injeta um registro fictício em texto puro
  (`"senha": "texto123"`) e confirma que a autenticação levanta
  `NaoAutorizadoError` — **falha fechada**.
- `usuario_repository.atualizar_senha` (usado apenas pelo fallback antigo) foi
  removido; `grep` não encontra referências.

### 4.3 Migração de legado no boot

Cenário: banco `/tmp/opencode/cs-legacy.db` criado com o schema atual e
`joao@email.com` forçado para `legado123` em texto puro.

1. Antes do boot: `SELECT senha` → `legado123`.
2. Boot da aplicação na porta 5067: `ensure_schema` chama
   `migrate_legacy_passwords`.
3. Depois do boot: valor → `scrypt:32768...` (162 caracteres).
4. `POST /login` com `joao@email.com`/`legado123` → **200**, com token e sem
   `senha` na resposta.
5. A rotina é idempotente: em bancos já migrados não há novos updates.

### 4.4 Não exposição

- `GET /usuarios` → todos os itens sem a chave `senha`.
- `GET /usuarios/<id>` → sem a chave `senha`.
- `POST /login` → `dados` sem `senha`.

## 5. Verificação estática

| Check | Resultado | Evidência |
|---|---|---|
| Estrutura alvo presente | **OK** | `routes/`, `controllers/`, `schemas/`, `services/`, `repositories/`, `models/`, `database/`, `middleware/`, `config.py`, `errors.py` |
| Rotas separadas do entrypoint | **OK** | `routes/*.py` (Blueprints); `app.py` chama `routes.init_app(app)` |
| Controllers só orquestram | **OK** | `controllers/__init__.py` — sem SQL, sem cálculo; chama `schemas` + `services` |
| Services com regra de negócio | **OK** | `services/pedido_service.py` (total, desconto, status), `services/usuario_service.py` (auth) |
| Repositories com acesso a dados | **OK** | `repositories/*.py`; só eles importam `get_db` para queries |
| Queries parametrizadas | **OK** | interpolações restantes são constantes (nomes de coluna/tabela fixos); valores de usuário usam `?` |
| Seed sem senha em texto puro | **OK** | `database/schema.py:USUARIOS_SEED` contém apenas hashes `scrypt:` |
| Login apenas com hash | **OK** | `services/usuario_service.py` usa `_hash_valido` + `check_password_hash`; sem igualdade de senha |
| Migração de legado | **OK** | `database/schema.py:migrate_legacy_passwords` chamada por `ensure_schema` em todo boot |
| Sem segredos hardcoded | **OK** | `SECRET_KEY` via env (`config.py`); grep de segredos sem literais |
| Arquivos órfãos removidos | **OK** | `controllers.py`, `models.py`, `database.py` antigos deletados; imports apontam para os pacotes novos |
| Config via ambiente | **OK** | `config.py` + `.env.example` |
| `git status` sem sobras | **OK** | sem `__pycache__`/`loja.db` de execução no diff |

## 6. Cruzamento com a auditoria (CRITICAL/HIGH)

| ID | Severidade | Classificação | Evidência da resolução |
|---|---|---|---|
| **SEC-01** SQL Injection | CRITICAL | **RESOLVIDO** | `repositories/*.py` usam `?`; grep confirma que nenhuma interpolação carrega entrada de usuário; smoke: `?q=' OR '1'='1` → `total:0` e `POST /login` com injeção → `401`. `/admin/query` (SQL arbitrário) removida → `404`. |
| **SEC-02** Credencial hardcoded | CRITICAL | **RESOLVIDO** | `SECRET_KEY` lida de env em `config.py`; nenhum literal no código; `services/health_service.py` não devolve `secret_key`/`db_path`/`debug` (validado: `/health` só traz 5 campos). |
| **SEC-03** Senhas em texto plano | CRITICAL | **RESOLVIDO** | Seed grava hashes scrypt (162 chars, nenhum igual às senhas conhecidas); cadastro usa `generate_password_hash`; login usa somente `check_password_hash`; `migrate_legacy_passwords` re-hasheia legado no boot; `senha` ausente em `GET /usuarios`, `GET /usuarios/<id>` e `/login`; smoke rejeita texto puro (falha fechada). |
| **SEC-04** Rotas sem auth | HIGH | **RESOLVIDO** | `POST /admin/reset-db` protegida por `require_admin` (fail-closed). `/login` emite token de sessão assinado; `require_tipos` protege escrita: produtos (`POST`/`PUT`/`DELETE`) e status de pedido exigem `admin`; `POST /pedidos` exige `cliente` e só aceita o próprio `usuario_id`. `401` sem token, `403` com nível insuficiente. |
| **ARCH-01** Lógica no Controller | HIGH | **RESOLVIDO** | `controllers/__init__.py` — handlers curtos, sem `for`/cálculo/regra; regras em `services/produto_service.py`, `pedido_service.py`, `usuario_service.py`. |
| **ARCH-02** Dados no Controller | HIGH | **RESOLVIDO** | Nenhum `execute`/`get_db` em `controllers/` ou `app.py`; SQL concentrado em `repositories/` e `services/admin_service.py`. |
| **QUAL-02** Validação ausente/frágil | HIGH | **RESOLVIDO** | `schemas/validators.py` valida presença, tipo e `get_json(silent=True)`; smoke valida `400` para body ausente, tipo textual, faixa e obrigatoriedade. |

**Resultado: 3/3 CRITICAL e 4/4 HIGH resolvidos. Nenhum item CRITICAL/HIGH pendente.**

## 7. MEDIUM/LOW (não bloqueiam)

| ID | Severidade | Classificação | Observação |
|---|---|---|---|
| ARCH-03 Model duplo | MEDIUM | **RESOLVIDO** | `models.py` eliminado; papéis separados. |
| QUAL-01 God File | MEDIUM | **RESOLVIDO** | maior arquivo 139 LOC (antes 314). |
| QUAL-02b Estoque não atômico | MEDIUM | **RESOLVIDO** | `UPDATE ... WHERE estoque >= ?` + `BEGIN IMMEDIATE` + rollback; smoke confirma que pedido rejeitado não debita estoque. |
| QUAL-03 Erro genérico | MEDIUM | **RESOLVIDO** | `middleware/error_handler.py` central; `500` genérico + `logger.exception`. |
| QUAL-04 Estado global mutável | MEDIUM | **RESOLVIDO** | `database/connection.py` usa `flask.g` por request + teardown. |
| PERF-01 N+1 | MEDIUM | **RESOLVIDO (resíduo documentado)** | Listagens usam JOIN único; gravação de pedido reusa a linha da validação. Resta 1 query por item na validação de estoque — reduzido de 2N+1, sem impacto de contrato. |
| SEC-06 Log sensível | LOW | **RESOLVIDO** | `services/notificacao_service.py` usa `logging` sem PII. |
| QUAL-05 Imports mortos | LOW | **RESOLVIDO** | imports mortos removidos; `SECRET_KEY` agora usada. |
| QUAL-07 Config hardcoded | LOW | **RESOLVIDO** | `config.py` + `.env.example`. |
| QUAL-08 Sem testes | LOW | **RESOLVIDO** | `tests/smoke_contract.py` (73 checks). |
| QUAL-06 Sem migrations | LOW | **FORA DE ESCOPO (por design)** | Schema segue inline em `database/schema.py` para preservar o boot; recomendado Alembic + constraints. |

## 8. Riscos e ressalvas

- **Escopo de leitura de SEC-04:** as rotas de escrita estão protegidas por nível
  (`admin`/`cliente`), mas `GET /usuarios`, `GET /pedidos`,
  `GET /pedidos/usuario/<id>` e `GET /relatorios/vendas` continuam públicas para
  preservar o contrato original. O achado SEC-04 tratava das rotas de escrita e
  administrativas; a proteção de leitura é melhoria futura.
- **Token sem revogação:** token é stateless e vale por `TOKEN_MAX_AGE_SECONDS`
  (padrão 8h); não há logout/revogação individual.
- **PERF-01 residual:** validação de itens em `POST /pedidos` faz 1 query por item.
- **QUAL-06:** sem migrations e sem `UNIQUE(email)`/`CHECK`/`FOREIGN KEY`.
- **Testes:** cobre contrato e segurança; não há suíte unitária de
  services/repositories.
- **Sem CI/CD:** o smoke test não está em pipeline.
- **Credenciais de desenvolvimento:** `admin123`/`123456`/`senha123` continuam
  documentadas no README e usadas nos testes, mas **não são persistidas em texto
  puro** em nenhum banco.

## 9. Recomendação final

**APROVADO**

A Fase 3 preservou o contrato de sucesso das 19 rotas do inventário, corrigiu
**3/3 CRITICAL** e **4/4 HIGH** e não introduziu regressões: **73/73 smoke
checks**, boot real validado, banco em repouso sem senhas em texto puro e
migração de legado comprovada. Não há item CRITICAL/HIGH pendente nem
classificação parcial nesse escopo.

As ressalvas restantes são melhorias incrementais de MEDIUM/LOW, não bloqueios:

1. Proteger também as rotas `GET` de usuários/pedidos/relatórios e adicionar
   revogação de token (SEC-04 residual de leitura).
2. Completar PERF-01 com `IN (...)` único na validação de itens.
3. Adotar migrations (Alembic) + constraints de integridade (QUAL-06).
4. Adicionar testes unitários de services/repositories e um pipeline de CI.

## 10. Notas e evidências

- **Comandos executados:**
  - Boot principal: `SECRET_KEY=etapa6-secret ADMIN_TOKEN=etapa6-admin-token DATABASE_PATH=/tmp/opencode/cs-etapa6.db PORT=5066 python app.py`
  - Boot legado: `SECRET_KEY=etapa6-secret ADMIN_TOKEN=etapa6-admin-token DATABASE_PATH=/tmp/opencode/cs-legacy.db PORT=5067 python app.py`
  - Smoke: `python tests/smoke_contract.py` → `73/73 checks passaram`
  - Estática: `grep -rnE "execute\(.*(\+|%|\.format\(|f['\"])" --include='*.py' .`
  - Segredos: `grep -rniE "(secret|password|token|api_key)\s*=\s*['\"][^'\"]{6,}" --include='*.py' .`
  - Senhas em repouso: `sqlite3 /tmp/opencode/cs-etapa6.db "SELECT email, senha FROM usuarios"`
- **Contrato de referência:** `reports/analysis-code-smells-project.md` §2.4 (19 rotas).
- **Achados de referência:** `reports/audit-code-smells-project.md` §2 e critérios §2.1.
- **Venv:** execuções em `/tmp/opencode/refactor-venv` (Flask 3.1.1). `requirements.txt` não foi alterado.
- **Limpeza:** `__pycache__` e bancos de execução em `/tmp/opencode`; `git status` sem sobras de runtime.
- **Fase 4:** nenhum arquivo de código-fonte foi modificado nesta etapa de validação (somente verificação + relatórios).
