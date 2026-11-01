# Refactor Report — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 3 — Refatoração).
> Data: 2026-10-22 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/code-smells-project`
> Baseado em: `reports/analysis-code-smells-project.md` e `reports/audit-code-smells-project.md`
> Confirmação do usuário: **Fase 3 aprovada com smoke test antes** e **remoção de `POST /admin/query`**.

## 1. Resumo

Reestruturação de monolito flat (4 arquivos na raiz) para arquitetura em camadas
(**Routes → Controllers → Services → Repositories**, com Models e Config),
corrigindo os achados CRITICAL e HIGH da auditoria.

### Antes

```
code-smells-project/
├── app.py           (88 LOC)  entrypoint + rotas + SQL admin
├── controllers.py   (292 LOC) HTTP + validação + regra de negócio
├── database.py      (86 LOC)  conexão global + DDL + seed
├── models.py        (314 LOC) SQL bruto + mapeamento + regra de negócio
└── requirements.txt
```

### Depois

```
code-smells-project/
├── app.py                    entrypoint: cria app, registra módulos (46 LOC)
├── config.py                 config via ambiente + constantes de domínio
├── errors.py                 erros de domínio (→ HTTP no handler central)
├── routes/                   registro de rotas por recurso (Blueprints)
│   ├── produto_routes.py  usuario_routes.py
│   ├── pedido_routes.py   relatorio_routes.py
│   └── __init__.py
├── controllers/__init__.py   orquestração request → schema → service → resposta
├── schemas/validators.py     validação de formato/tipo (QUAL-02)
├── services/                 regras de negócio, sem HTTP
│   ├── produto_service.py  usuario_service.py  pedido_service.py
│   ├── notificacao_service.py  health_service.py  admin_service.py
│   └── __init__.py
├── repositories/             único ponto de acesso a dados, queries parametrizadas
│   ├── produto_repository.py  usuario_repository.py  pedido_repository.py
│   └── __init__.py
├── models/produto.py         invariantes de entidade (Produto, ItemPedido)
├── database/                 connection.py (por request) + schema.py (DDL/seed)
├── middleware/               error_handler.py (erro central) + auth.py (admin)
├── tests/smoke_contract.py   smoke test de contrato (68 checks)
├── .env.example
└── reports/
```

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos-fonte `.py` | 4 | 31 |
| LOC (sem testes) | 780 | 1428 |
| Maior arquivo (LOC) | 314 (`models.py`) | 139 (`pedido_repository.py`) |
| Camadas | 0 (flat) | 8 (routes, controllers, schemas, services, repositories, models, database, middleware) |
| Queries parametrizadas | não | sim (100%) |
| Testes | 0 | 68 checks (smoke de contrato) |

O aumento de LOC reflete a separação de responsabilidades (um arquivo por
recurso/camada) e a extração de validação, erros e config — não crescimento
de complexidade em um único ponto.

## 2. Anti-patterns corrigidos

| ID | Severidade | Como foi resolvido | Evidência |
|---|---|---|---|
| **SEC-01** SQL Injection | CRITICAL | Todas as queries passaram a usar placeholders `?`; o endpoint `/admin/query` foi removido | `repositories/produto_repository.py`, `usuario_repository.py`, `pedido_repository.py`; remoção em `routes/relatorio_routes.py` |
| **SEC-02** Credencial hardcoded | CRITICAL | `SECRET_KEY` vem de `SECRET_KEY` env; `/health` deixou de devolver `secret_key`/`db_path`/`debug` | `config.py`, `app.py:22`, `services/health_service.py` |
| **SEC-03** Senhas em texto plano | CRITICAL | Hash com salt (`generate_password_hash`/`check_password_hash`); `senha` fora das respostas; upgrade transparente de seed legado no login | `services/usuario_service.py`, `repositories/usuario_repository.py:listar/buscar_por_id` |
| **SEC-04** Rotas sem auth | HIGH | `POST /admin/reset-db` exige `Authorization: Bearer <ADMIN_TOKEN>` (fail-closed). `/login` emite token de sessão assinado; escrita de produtos exige nível `admin`, cadastro de pedido exige nível `cliente` (só para o próprio usuário) e status de pedido exige `admin` | `middleware/auth.py`, `services/auth_service.py`, `routes/produto_routes.py`, `routes/pedido_routes.py`, `routes/relatorio_routes.py:36` |
| **SEC-06** PII/dados sensíveis em log | LOW | `print` de e-mails e notificações substituídos por `logging` sem PII | `services/notificacao_service.py`; `controllers/__init__.py` sem `print` de e-mail |
| **ARCH-01** Lógica de negócio no Controller | HIGH | Regras (cálculo de total, estoque, faixas de desconto, status) extraídas para services; controllers só orquestram | `services/pedido_service.py`, `services/produto_service.py`, `controllers/__init__.py` |
| **ARCH-02** Acesso a dados no Controller | HIGH | Todo SQL saiu de `controllers.py` e `app.py` para repositories | `repositories/`; `services/admin_service.py`; `services/health_service.py` |
| **ARCH-03** Model com 3 papéis | MEDIUM | `models.py` deixou de existir; persistência → repositories, regra → services, invariantes → `models/produto.py` | `models/produto.py`, `repositories/`, `services/` |
| **QUAL-01** God File | MEDIUM | `models.py` (314) e `controllers.py` (292) divididos por domínio nas camadas | maior arquivo agora tem 139 LOC |
| **QUAL-02** Validação ausente/frágil | HIGH | `schemas/validators.py` valida schema, obrigatoriedade e tipos antes do service; `get_json(silent=True)` evita 500 | `schemas/validators.py`, `controllers/__init__.py` |
| **QUAL-02b** Estoque não atômico | MEDIUM | Débito condicional `UPDATE ... WHERE estoque >= ?` + transação `BEGIN IMMEDIATE` com rollback | `repositories/pedido_repository.py:criar` |
| **QUAL-03** Erro genérico com vazamento | MEDIUM | Um handler central traduz erros de domínio e devolve 500 genérico, logando o detalhe | `middleware/error_handler.py`, `errors.py` |
| **QUAL-04** Estado global mutável | MEDIUM | Conexão passou a ter escopo de request (`flask.g`) com teardown; sem singleton | `database/connection.py` |
| **QUAL-05** Imports/config mortos | LOW | Removidos `import os`/`import sqlite3` mortos; `SECRET_KEY` agora é usada de verdade | `database/`, `models/` |
| **QUAL-07** Config hardcoded | LOW | Host, porta, debug, caminho do banco e versão/ambiente lidos de env | `config.py`, `.env.example` |
| **QUAL-08** Sem testes | LOW | Smoke test de contrato com 68 checks (inclui autorização por nível) | `tests/smoke_contract.py` |

### Não resolvidos nesta fase (documentados como trabalho futuro)

| ID | Severidade | Motivo |
|---|---|---|
| **PERF-01** N+1 | MEDIUM | **Corrigido parcialmente:** as listagens de pedidos (`listar`, `listar_por_usuario`) usam JOIN único. A gravação de pedido deixou de reconsultar produtos (reusa a linha da validação). Resta apenas o cenário de 1 query por item na validação — reduzido de 2N+1 para N+1 e sem impacto no contrato. |
| **QUAL-06** Sem migrations | LOW | Schema segue inline em `database/schema.py` para preservar o comportamento de boot (criação no primeiro acesso). Adotar Alembic/Flask-Migrate é o passo dedicado recomendado, junto de `UNIQUE(email)`, `CHECK` e `FOREIGN KEY`. |

## 3. Mudanças de contrato (deliberadas)

Todas são exigidas pela auditoria e foram validadas pelo smoke test.

| Rota | Mudança | Justificativa |
|---|---|---|
| `POST /admin/query` | **Removida** (404) | Executava SQL arbitrário do body (SEC-01/SEC-04) — decisão confirmada pelo usuário |
| `POST /admin/reset-db` | Exige `Authorization: Bearer <ADMIN_TOKEN>`; 401 sem token, 403 se `ADMIN_TOKEN` ausente no processo | SEC-04 |
| `POST /login` | Passa a devolver `token` de sessão assinado (além de `dados`, sem `senha`) | SEC-04 |
| `POST`/`PUT`/`DELETE /produtos` | Exigem `Authorization: Bearer <token>` de usuário nível `admin`; 401 sem token, 403 com nível insuficiente | SEC-04 |
| `POST /pedidos` | Exige nível `cliente`; o `usuario_id` do body deve ser o do usuário autenticado; 401 sem token, 403 para outro usuário/nível | SEC-04 |
| `PUT /pedidos/<id>/status` | Exige nível `admin`; 401 sem token, 403 com nível insuficiente | SEC-04 |
| `GET /health` | Não devolve mais `secret_key`, `db_path` nem `debug` | SEC-02/QUAL-07 |
| `GET /usuarios`, `GET /usuarios/<id>` | Não devolvem mais o campo `senha` | SEC-03 |
| `POST /produtos` (payload malformado) | Passa a devolver 400 com mensagem de validação (antes podia virar 500) | QUAL-02 |
| `POST /pedidos` (produto/usuário inexistente) | Mantido 400 com `{"erro": ..., "sucesso": false}` | preservação de contrato |

Formato de resposta preservado em todas as rotas de sucesso: `{"dados": ..., "sucesso": true}`
(e `mensagem` onde existia). Erros agora são sempre `{"erro": ..., "sucesso": false}`.

## 4. Smoke test por endpoint

**Antes da refatoração** (código original via `git HEAD`): **45/45 checks** — contrato travado,
incluindo os comportamentos inseguros então vigentes (SQLi vazando tabela, `secret_key` no
`/health`, senha exposta, `/admin/query` executando SQL).

**Depois da refatoração**: **68/68 checks** (68 = 45 originais + 13 de segurança/validação + 10 de autorização por nível).

### Boot real (não apenas test client)

`SECRET_KEY=boot-secret ADMIN_TOKEN=... PORT=5099 python app.py` subiu sem erros;
todas as rotas exercitadas via `curl`:

| # | Método | Path | Status | Resultado |
|---|---|---|---|---|
| 1 | GET | `/` | 200 | Lista os 6 recursos |
| 2 | GET | `/health` | 200 | Contadores; sem campos sensíveis |
| 3 | GET | `/produtos` | 200 | 10 itens do seed |
| 4 | GET | `/produtos/busca?q=Mouse` | 200 | `total: 1` |
| 5 | GET | `/produtos/1` | 200 | Notebook Gamer 5999.99 |
| 6 | GET | `/produtos/9999` | 404 | `Produto não encontrado` |
| 7 | POST | `/produtos` (sem token) | 401 | `Token de acesso ausente` |
| 7b | POST | `/produtos` (token cliente) | 403 | `Perfil sem permissão` |
| 7c | POST | `/produtos` (token admin) | 201 | `{"dados":{"id":11}}` |
| 8 | POST | `/produtos` (sem preço, admin) | 400 | `Preço é obrigatório` |
| 9 | PUT | `/produtos/11` (admin) | 200 | atualização refletida |
| 10 | GET | `/usuarios` | 200 | 3 usuários, **sem `senha`** |
| 11 | POST | `/usuarios` | 201 | `{"dados":{"id":4}}` |
| 12 | POST | `/login` | 200 | devolve `token` de sessão; sem senha |
| 13 | POST | `/login` (senha errada) | 401 | `Email ou senha inválidos` |
| 14 | POST | `/pedidos` (token cliente) | 201 | `total: 479.7`, estoque debitado |
| 14b | POST | `/pedidos` (sem token) | 401 | `Token de acesso ausente` |
| 14c | POST | `/pedidos` (token admin) | 403 | `Perfil sem permissão` |
| 14d | POST | `/pedidos` (outro `usuario_id`) | 403 | `Cliente só pode criar pedido para si mesmo` |
| 15 | GET | `/pedidos` | 200 | 1 pedido com itens e `produto_nome` |
| 16 | GET | `/pedidos/usuario/2` | 200 | 1 pedido com itens |
| 17 | PUT | `/pedidos/1/status` (admin) | 200 | `Status atualizado` |
| 17b | PUT | `/pedidos/1/status` (sem token) | 401 | `Token de acesso ausente` |
| 18 | GET | `/relatorios/vendas` | 200 | agregados e desconto corretos |
| 19 | POST | `/admin/query` | 404 | **removida** |
| 20 | POST | `/admin/reset-db` (sem token) | 401 | `Token administrativo ausente` |
| 21 | POST | `/admin/reset-db` (com token) | 200 | base limpa |

### Verificações de segurança no smoke test

- `GET /produtos/busca?q=' OR '1'='1` → `total: 0` (antes: 11) — **SQLi neutralizada**.
- `POST /login` com `' OR '1'='1` → 401 — **bypass de login neutralizado**.
- Senha persistida como `scrypt:32768:8:...` — **hash com salt**.
- Pedido rejeitado por estoque **não debita** estoque (rollback verificado).
- `POST /produtos` sem token → 401; com token de cliente → 403; com admin → 201.
- `POST /pedidos` sem token → 401; com admin → 403; para outro usuário → 403;
  com cliente dono → 201.
- Token de sessão é assinado com `SECRET_KEY`, expira em `TOKEN_MAX_AGE_SECONDS`
  e o nível é relido do banco a cada requisição.

## 5. Checklist da Fase 3

- [x] Aplicação sobe sem erros (`python app.py`, porta 5099)
- [x] Toda rota inventariada responde no mesmo path/verbo; formato preservado
- [x] Rotas de escrita rejeitam payload malformado com 400
- [x] Rotas de escrita exigem token de sessão e nível adequado (SEC-04)
- [x] Nenhuma query interpolada — grep confirma que f-strings só usam nomes de coluna/tabela fixos
- [x] Nenhum segredo literal no código (`minha-chave-super-secreta-123` removida)
- [x] Responses não expõem `senha`, `secret_key`, `db_path`
- [x] Sem `except Exception` engolindo erro — handler central em `middleware/error_handler.py`
- [x] Arquivos antigos removidos (`controllers.py`, `models.py`, `database.py` deletados)
- [x] `git status` sem sobras (`__pycache__` e `loja.db` de execução removidos)

## 6. Estratégia de migração de senhas (Padrão 6)

O seed original gravava senhas em texto puro (`admin123`, `123456`, `senha123`).
Para não quebrar o login dos usuários existentes:

1. Novos usuários: hash com salt desde a criação (`services/usuario_service.py:criar`).
2. Usuários legados: `autenticar` compara o texto puro quando o valor armazenado
   não tem prefixo de hash (`pbkdf2:`/`scrypt:`/`argon2:`) e, no sucesso,
   **re-hasheia** via `usuario_repository.atualizar_senha` (upgrade transparente).
3. Nenhuma resposta de API carrega o campo `senha`.

**Recomendação:** rodar um reset de senha em lote ou re-hash de todos os
registros legados, eliminando a comparação em texto puro do caminho de login.

## 7. Limitações e trabalho futuro

- **Autenticação de rotas de escrita:** `/login` emite token assinado
  (`services/auth_service.py`), e as rotas de produto/pedido de escrita exigem
  o nível correspondente (`admin`/`cliente`). Rotas de leitura (`GET /usuarios`,
  `GET /pedidos`, `GET /pedidos/usuario/<id>`, `GET /relatorios/vendas`)
  continuam públicas para preservar o contrato original; protegê-las é o
  próximo passo recomendado de SEC-04.
- **Token stateless:** não há revogação individual antes do vencimento
  (`TOKEN_MAX_AGE_SECONDS`, padrão 8h). Para logout/revogação, adicionar
  lista de revogação ou versão de token por usuário.
- **PERF-01 residual:** a validação de itens em `POST /pedidos` ainda faz 1 query
  por item; um `IN (...)` único resolveria por completo.
- **QUAL-06/Migrations:** adotar Alembic/Flask-Migrate e reforçar integridade
  (`UNIQUE(email)`, `CHECK(preco >= 0)`, `CHECK(estoque >= 0)`, `FOREIGN KEY`).
- **QUAL-08/Testes:** o smoke test cobre contrato e segurança; falta suíte unitária
  de services (cálculo de desconto, regras de estoque) e de repositórios.
- **CI/CD:** nenhum pipeline; incluir `python tests/smoke_contract.py` como gate.
- **ERROR-HANDLER:** o handler de `Exception` usa `logger.exception`; em produção,
  configurar destino de log e desligar `DEBUG`.
- **Venv de validação:** as execuções usaram um venv isolado em `/tmp/opencode/refactor-venv`
  (Flask 3.1.1 + pytest); não foi adicionado ao repositório. `requirements.txt` não
  foi alterado (nenhuma dependência nova foi introduzida).

## 8. Atualização — autorização por nível (SEC-04)

A primeira rodada da Fase 3 protegeu apenas `POST /admin/reset-db`. Esta
atualização fecha o escopo de escrita de negócio apontado na auditoria:

| Rota | Nível exigido | Regra adicional |
|---|---|---|
| `POST /produtos` | `admin` | — |
| `PUT /produtos/<id>` | `admin` | — |
| `DELETE /produtos/<id>` | `admin` | — |
| `POST /pedidos` | `cliente` | `usuario_id` deve ser o do usuário autenticado |
| `PUT /pedidos/<id>/status` | `admin` | — |

**Fluxo:** `POST /login` autentica pelo seed (`admin@loja.com`/`admin123`,
`joao@email.com`/`123456`, `maria@email.com`/`senha123`), lê `usuarios.tipo` e
emite `token` assinado com `SECRET_KEY` via `itsdangerous`
(`services/auth_service.py`). O guard `require_tipos` valida assinatura e
validade, relê o usuário no banco e compara o nível; ausência/expiração do
token → `401`, nível insuficiente → `403`.

**Fora do escopo desta atualização:** rotas `GET` de usuários, pedidos e
relatórios continuam públicas (preservação de contrato); `POST /usuarios`
segue aberto como cadastro público. Proteção de leitura e rate limiting ficam
como trabalho futuro.

**Validação:** `python tests/smoke_contract.py` → **68/68 checks**.
