# Architecture Audit Report — code-smells-project

================================
PHASE 1: PROJECT ANALYSIS
================================
Language(s): Python — 4 módulos `.py`, 780 linhas
Runtime(s): CPython 3.12.11 observado no ambiente local; versão mínima do projeto não declarada
Framework(s): Flask 3.1.1; Flask-CORS 5.0.1
Dependencies: Flask, Flask-CORS e `sqlite3` da biblioteca padrão
Persistence: SQLite local; tabelas `produtos`, `usuarios`, `pedidos` e `itens_pedido`
Domain: API de e-commerce para catálogo, usuários, autenticação, pedidos e vendas
Architecture: monólito parcialmente dividido em bootstrap, controllers, models e database, com responsabilidades cruzadas
Entry points: `app.py`; `python app.py` é o comando documentado, mas não foi executado
Source files: 5 artefatos técnicos, 782 linhas — 4 fontes Python e `requirements.txt`
Contracts: 19 operações HTTP explícitas; `HEAD`/`OPTIONS` automáticos não contados
Tests: nenhum teste, framework ou comando de teste encontrado
================================

## Metadata

- **Codebase root:** `/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project`
- **Delivery repository root:** `/home/matheussouza/learn/mba-ia-refactor-projects-skill`
- **Version-control snapshot:** commit `6d1ce6248c3e956801010a89d8bdaab48029bf30`, branch `main...origin/main`
- **Audited source fingerprint:** tree `2a6dd2e631dbd7d1266664d13fd2d0afb0dce3c9` em `6d1ce6248c3e956801010a89d8bdaab48029bf30`; `.codex/` preexistente excluída
- **Preexisting changes:** `code-smells-project/.codex/` já estava não rastreado; os seis arquivos rastreados da aplicação estavam limpos
- **Audited at:** `2026-07-22T20:17:19-04:00`
- **Scope:** `app.py`, `controllers.py`, `models.py`, `database.py`, `requirements.txt`; `README.md` usado apenas como evidência documental
- **Exclusions:** `.venv/`, `__pycache__/`, `.codex/`, `loja.db` e artefatos gerados
- **Source files:** 5
- **Lines inspected:** 782 linhas técnicas; 12 linhas adicionais de documentação
- **Report path:** `reports/audit-project-1.md`
- **Phase 1–2 filesystem changes:** este relatório somente

## Project Analysis

| Attribute | Result | Evidence | Confidence |
|---|---|---|---|
| Language/runtime | Python; ambiente local CPython 3.12.11, sem requisito de versão declarado | [app.py:1](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:1), `.venv/pyvenv.cfg:1-6` | HIGH para linguagem; MEDIUM para runtime requerido |
| Build/dependencies | Sem build; instalação documentada via `pip install -r requirements.txt` | [requirements.txt:1](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/requirements.txt:1), [README.md:5](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/README.md:5) | HIGH |
| Framework/interfaces | Flask 3.1.1, Flask-CORS 5.0.1, 19 operações HTTP | [app.py:1](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:1), [app.py:11](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:11) | HIGH |
| Persistence/integrations | SQLite em arquivo; notificações externas são apenas `print`, sem integração real | [database.py:4](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:4), [controllers.py:208](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:208) | HIGH |
| Domain | Catálogo, usuários, login, pedidos, estoque e relatório de vendas | [app.py:11](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:11), [models.py:133](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:133) | HIGH |
| Current architecture | Monólito em camadas nominais, mas com domínio, SQL, apresentação, configuração e bootstrap misturados | [app.py:6](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:6), [controllers.py:5](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:5), [models.py:4](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:4) | HIGH |
| Units/entry points | Uma API; entrada `app.py`; comando `python app.py` classificado como DISCOVERED, não validado | [app.py:80](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:80), [README.md:7](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/README.md:7) | HIGH |
| Tests | Ausentes | Inventário integral, excluídos caches/vendor | HIGH |

## Public Contract Baseline

Nenhuma rota possui autenticação ou autorização observável. `CORS(app)` aplica CORS globalmente.

| Type | Identity | Handler/location | Input/auth | Expected output/error/effect |
|---|---|---|---|---|
| HTTP | `GET /` | `index`, [app.py:32](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:32) | Sem entrada; sem auth | `200`, mensagem, versão e mapa de endpoints |
| HTTP | `GET /produtos` | `listar_produtos`, [controllers.py:5](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:5) | Sem auth | `200 {dados, sucesso}`; `500 {erro}` |
| HTTP | `GET /produtos/busca` | `buscar_produtos`, [controllers.py:111](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:111) | Query `q`, `categoria`, `preco_min`, `preco_max`; sem auth | `200 {dados,total,sucesso}`; `500 {erro}` |
| HTTP | `GET /produtos/<id>` | `buscar_produto`, [controllers.py:14](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:14) | ID inteiro; sem auth | `200` produto; `404`; `500` |
| HTTP | `POST /produtos` | `criar_produto`, [controllers.py:24](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:24) | JSON `nome`, `preco`, `estoque`; opcionais `descricao`, `categoria`; sem auth | `201` com ID; `400`; `500`; persiste produto |
| HTTP | `PUT /produtos/<id>` | `atualizar_produto`, [controllers.py:64](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:64) | ID e JSON completo; sem auth | `200`; `400`; `404`; `500`; atualiza produto |
| HTTP | `DELETE /produtos/<id>` | `deletar_produto`, [controllers.py:98](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:98) | ID; sem auth | `200`; `404`; `500`; remove produto |
| HTTP | `GET /usuarios` | `listar_usuarios`, [controllers.py:128](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:128) | Sem auth | `200` com usuários, atualmente incluindo campo de senha; `500` |
| HTTP | `GET /usuarios/<id>` | `buscar_usuario`, [controllers.py:136](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:136) | ID; sem auth | `200` com usuário e senha; `404`; `500` |
| HTTP | `POST /usuarios` | `criar_usuario`, [controllers.py:146](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:146) | JSON `nome`, `email`, `senha`; sem auth | `201` com ID; `400`; `500`; persiste usuário |
| HTTP | `POST /login` | `login`, [controllers.py:167](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:167) | JSON `email`, `senha`; sem auth | `200` com usuário; `400`; `401`; `500` |
| HTTP | `POST /pedidos` | `criar_pedido`, [controllers.py:188](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:188) | JSON `usuario_id`, `itens[{produto_id,quantidade}]`; sem auth | `201` com ID/total; `400`; `500`; cria pedido e altera estoque |
| HTTP | `GET /pedidos` | `listar_todos_pedidos`, [controllers.py:229](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:229) | Sem auth | `200 {dados,sucesso}`; `500` |
| HTTP | `GET /pedidos/usuario/<usuario_id>` | `listar_pedidos_usuario`, [controllers.py:222](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:222) | ID; sem auth | `200` com pedidos e itens; `500` |
| HTTP | `PUT /pedidos/<pedido_id>/status` | `atualizar_status_pedido`, [controllers.py:237](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:237) | JSON `status`; sem auth | `200`; `400`; `500`; altera status |
| HTTP | `GET /relatorios/vendas` | `relatorio_vendas`, [controllers.py:257](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:257) | Sem auth | `200` com totais, faturamento, desconto e ticket médio; `500` |
| HTTP | `GET /health` | `health_check`, [controllers.py:264](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:264) | Sem auth | `200` com estado, contagens e configuração sensível; `500` |
| HTTP | `POST /admin/reset-db` | `reset_database`, [app.py:47](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:47) | Sem auth | `200`; apaga todos os registros; falhas podem usar resposta HTML padrão |
| HTTP | `POST /admin/query` | `executar_query`, [app.py:59](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:59) | JSON `sql`; sem auth | `200` com linhas ou confirmação; `400`; `500`; executa SQL arbitrário |

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | 5 |
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 2 |
| **Total** | **15** |

**Acceptance check:** `>= 5 verified findings: PASS`; `>= 1 CRITICAL or HIGH: PASS`.

## Deprecated API Check

- **Status:** nenhuma ocorrência confirmada.
- **Versions inspected:** CPython 3.12.11, Flask 3.1.1 e Flask-CORS 5.0.1, comprovados por manifesto e metadados do ambiente local.
- **Sources checked:** fontes/imports, `requirements.txt`, metadados instalados, [API oficial do Flask 3.1](https://flask.palletsprojects.com/en/stable/api/), [changelog do Flask](https://flask.palletsprojects.com/en/stable/changes/), [documentação oficial do `sqlite3` 3.12](https://docs.python.org/3.12/library/sqlite3.html) e [API do Flask-CORS](https://flask-cors.readthedocs.io/en/latest/api.html).
- **Resultado:** `route`, `add_url_rule`, `jsonify`, `request.get_json`, `sqlite3.connect`, `execute`, `commit` e `CORS(app)` não apresentam prova de depreciação nas versões observadas. As depreciações documentadas de `sqlite3.version`, `sqlite3.version_info` e adaptadores padrão não são usadas.
- **Candidates not counted:** nenhum.

Cobertura do catálogo: AP-01 a AP-10 e AP-13/AP-14 possuem findings; AP-11 não apresentou API deprecated; AP-12 não se aplica porque os supostos envios de e-mail/SMS/push são apenas mensagens em `stdout`, sem I/O externo real.

## Findings

### F-001 — [CRITICAL] Endpoint público executa SQL arbitrário

- **Catalog rule:** AP-01 — Injection ou execução arbitrária
- **Location:** [app.py:59-78](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:59)
- **Evidence:** o campo `sql` do JSON é passado diretamente a `cursor.execute`; comandos não-`SELECT` são confirmados com `commit`.
- **Impact:** qualquer cliente pode ler, alterar ou apagar dados e modificar o schema.
- **Recommendation:** aposentar a execução genérica ou substituí-la por operações administrativas fechadas, autenticadas e parametrizadas.
- **Transformation:** T02 + T09.
- **Validation:** payloads SQL arbitrários devem ser rejeitados; operações administrativas autorizadas devem permanecer explicitamente testadas.
- **Confidence:** HIGH.

### F-002 — [CRITICAL] SQL injection em múltiplos fluxos públicos

- **Catalog rule:** AP-01 — Injection
- **Location:** [controllers.py:24](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:24) → [models.py:43](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:43); [controllers.py:111](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:111) → [models.py:285](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:285); [controllers.py:167](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:167) → [models.py:105](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:105)
- **Evidence:** nome, descrição, categoria, busca, e-mail e senha controlados pelo cliente são concatenados em SQL.
- **Impact:** leitura indevida, bypass de login, corrupção e destruição de dados.
- **Recommendation:** placeholders para todos os valores e construção estrutural por allowlist.
- **Transformation:** T02.
- **Validation:** testes adversariais em criação, atualização, busca, cadastro e login.
- **Confidence:** HIGH.

### F-003 — [CRITICAL] Ausência de autenticação e autorização

- **Catalog rule:** AP-03 — Autenticação insegura
- **Location:** [app.py:6-30](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:6), [app.py:47-76](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:47)
- **Evidence:** as rotas são registradas diretamente, sem middleware ou verificação de identidade/papel; isso inclui reset, consulta SQL, escrita de produtos, usuários, pedidos e relatórios.
- **Impact:** acesso anônimo a dados pessoais e operações administrativas/destrutivas.
- **Recommendation:** autenticação verificável e matriz explícita de autorização por rota e proprietário.
- **Transformation:** T09.
- **Validation:** testes `401/403` por rota e testes positivos por papel.
- **Confidence:** HIGH.

### F-004 — [CRITICAL] Senhas armazenadas e comparadas em texto puro

- **Catalog rule:** AP-03 — Criptografia insegura
- **Location:** [database.py:27-34](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:27), [database.py:75-83](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:75), [models.py:105-130](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:105)
- **Evidence:** coluna e consultas trabalham com senha literal; usuários iniciais possuem credenciais padrão embutidas.
- **Impact:** comprometimento imediato das contas se banco ou código for exposto.
- **Recommendation:** hasher adaptativo, migração segura e remoção de credenciais padrão.
- **Transformation:** T09.
- **Validation:** banco nunca contém a senha original; login correto funciona e comparação direta não.
- **Confidence:** HIGH.

### F-005 — [CRITICAL] Credenciais e segredo de aplicação expostos nas respostas

- **Catalog rule:** AP-02 — Segredo ou dado sensível exposto
- **Location:** [models.py:72-103](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:72), [controllers.py:128-144](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:128), [controllers.py:276-290](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:276), [app.py:7](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:7)
- **Evidence:** consultas de usuário serializam o campo de senha; `/health` devolve o segredo configurado e detalhes internos.
- **Impact:** vazamento de contas, falsificação de dados assinados e reconhecimento da infraestrutura.
- **Recommendation:** DTOs públicos seguros, health check mínimo e segredo fornecido externamente.
- **Transformation:** T01 + T08 + T09.
- **Validation:** respostas não contêm senha, chave, path interno ou flag de debug.
- **Confidence:** HIGH.

### F-006 — [HIGH] Conexão SQLite global compartilhada entre requisições

- **Catalog rule:** AP-06 — Estado global mutável
- **Location:** [database.py:4-11](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:4)
- **Evidence:** uma única conexão global é reutilizada, a proteção de thread é desabilitada e não existe fechamento por request.
- **Impact:** cursores e transações podem atravessar requisições; há risco de corrida, lock e vazamento de estado.
- **Recommendation:** conexão por request/unidade de trabalho, fechamento em teardown e dependência injetável.
- **Transformation:** T05.
- **Validation:** requisições concorrentes isoladas e verificação de fechamento/rollback.
- **Confidence:** HIGH.

### F-007 — [HIGH] Invariantes de pedido e integridade referencial não são garantidas

- **Catalog rule:** AP-07 — Integridade quebrada
- **Location:** [database.py:14-53](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:14), [models.py:133-168](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:133), [models.py:275-283](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:275)
- **Evidence:** não há FKs, `CHECK`, `UNIQUE` ou campos obrigatórios relevantes; quantidade negativa é aceita e aumenta estoque; usuário inexistente pode receber pedido; cancelamento altera apenas o status.
- **Impact:** totais negativos, estoque artificialmente aumentado, registros órfãos e cancelamentos sem restituição.
- **Recommendation:** invariantes no domínio e no schema, validação positiva e política transacional de cancelamento.
- **Transformation:** T06 + T08.
- **Validation:** testes para quantidade zero/negativa, usuário inexistente, remoção referenciada e cancelamento.
- **Confidence:** HIGH.

### F-008 — [HIGH] Falhas intermediárias não fazem rollback

- **Catalog rule:** AP-07 — Operação não atômica
- **Location:** [models.py:133-169](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:133), [controllers.py:218-220](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:218)
- **Evidence:** criação de pedido executa múltiplos inserts/updates e só confirma no final; exceções são capturadas sem rollback. A conexão global pode confirmar posteriormente a transação pendente.
- **Impact:** pedidos, itens e estoque podem ficar parcialmente modificados.
- **Recommendation:** unidade de trabalho explícita com commit/rollback e conexão isolada.
- **Transformation:** T05 + T06.
- **Validation:** injetar falha após cada write e confirmar estado integralmente revertido.
- **Confidence:** HIGH.

### F-009 — [HIGH] `models.py` concentra persistência, domínio e serialização

- **Catalog rule:** AP-04 — God module
- **Location:** [models.py:4-314](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:4)
- **Evidence:** o módulo implementa CRUD de produtos/usuários, autenticação, cálculo e transação de pedidos, serialização e relatório.
- **Impact:** alto raio de mudança, testes dependentes de banco e acoplamento entre domínios.
- **Recommendation:** separar modelos/invariantes, casos de uso e repositories por domínio.
- **Transformation:** T03 + T04.
- **Validation:** testes unitários de domínio sem Flask ou SQLite real.
- **Confidence:** HIGH.

### F-010 — [HIGH] Controllers misturam HTTP, regras, integração e infraestrutura

- **Catalog rule:** AP-05 — Fat controller
- **Location:** [controllers.py:24-62](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:24), [controllers.py:188-220](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:188), [controllers.py:237-290](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:237)
- **Evidence:** handlers validam políticas, orquestram pedidos, simulam notificações, consultam banco diretamente e formatam respostas.
- **Impact:** casos de uso só podem ser exercitados dentro de contexto Flask e são difíceis de substituir/testar.
- **Recommendation:** adapters HTTP finos chamando controllers/casos de uso independentes.
- **Transformation:** T03 + T04.
- **Validation:** controllers testáveis com repositories/notificadores falsos.
- **Confidence:** HIGH.

### F-011 — [MEDIUM] Consultas N+1 ao carregar pedidos

- **Catalog rule:** AP-08 — N+1 queries
- **Location:** [models.py:171-233](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:171)
- **Evidence:** cada lista executa uma consulta de pedidos, uma por pedido para itens e uma por item para o produto: `1 + N + Σ(itens)`.
- **Impact:** latência e carga no banco crescem diretamente com pedidos e itens.
- **Recommendation:** consulta com `JOIN`, lote de IDs ou mapa pré-carregado.
- **Transformation:** T07.
- **Validation:** contador de queries constante ou limitado independentemente do número de itens.
- **Confidence:** HIGH.

### F-012 — [MEDIUM] Validação de produto duplicada e divergente

- **Catalog rule:** AP-09 — Regra/validação duplicada
- **Location:** [controllers.py:24-54](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:24), [controllers.py:64-92](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:64)
- **Evidence:** campos obrigatórios, preço e estoque são repetidos; atualização não aplica limites de nome nem categorias válidas usadas na criação.
- **Impact:** o mesmo produto aceita estados diferentes conforme a operação.
- **Recommendation:** validator/policy única no domínio.
- **Transformation:** T08.
- **Validation:** matriz idêntica de invariantes para criação e atualização.
- **Confidence:** HIGH.

### F-013 — [MEDIUM] Tradução de erros inconsistente e vazamento de detalhes

- **Catalog rule:** AP-10 — Tratamento de erro inadequado
- **Location:** [controllers.py:5-292](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:5), [app.py:47-78](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:47)
- **Evidence:** `except Exception` devolve `str(e)`; alguns erros escapam para HTML padrão; updates ignoram `rowcount` e retornam sucesso mesmo sem registro; logging usa `print`.
- **Impact:** vazamento de SQL/infraestrutura, falso sucesso e diagnóstico operacional inconsistente.
- **Recommendation:** erros tipados, mapper HTTP central e logging estruturado.
- **Transformation:** T10.
- **Validation:** matriz uniforme de `400/401/403/404/409/500`, sem detalhes internos.
- **Confidence:** HIGH.

### F-014 — [LOW] Configuração operacional embutida e contraditória

- **Catalog rule:** AP-13 — Configuração dispersa
- **Location:** [app.py:6-9](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:6), [app.py:80-88](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/app.py:80), [database.py:4-5](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:4), [controllers.py:285-289](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/controllers.py:285)
- **Evidence:** debug, host, porta, database path, CORS e nome de ambiente estão embutidos; a resposta diz produção enquanto debug está habilitado.
- **Impact:** implantação insegura e necessidade de editar código por ambiente.
- **Recommendation:** configuração tipada por ambiente, com defaults apenas de desenvolvimento.
- **Transformation:** T01.
- **Validation:** boot em configurações de teste/desenvolvimento/produção sem editar fontes.
- **Confidence:** HIGH.

### F-015 — [LOW] Imports mortos e dependências aparentes inexistentes

- **Catalog rule:** AP-14 — Higiene e legibilidade
- **Location:** [models.py:1-2](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/models.py:1), [database.py:1-2](/home/matheussouza/learn/mba-ia-refactor-projects-skill/code-smells-project/database.py:1)
- **Evidence:** `sqlite3` em `models.py` e `os` em `database.py` são importados, mas nunca usados.
- **Impact:** obscurece dependências reais e aumenta ruído de manutenção.
- **Recommendation:** remover imports mortos durante a separação arquitetural.
- **Transformation:** T08.
- **Validation:** análise estática sem imports não utilizados.
- **Confidence:** HIGH.

## Proposed Refactoring Plan

| Order | Finding IDs | Transformation | Files/roles affected | Risk | Validation |
|---:|---|---|---|---|---|
| 1 | F-005, F-014 | T01 — configuração externa | `app.py`, `database.py`, novo `config.py` | Boot incompatível sem variáveis | Boot com configuração temporária e falha segura quando segredo obrigatório faltar |
| 2 | F-004, F-005 | T09 — autenticação, hashing e DTO seguro | usuários, login, serializers, schema/migração | Migração de senhas e mudança deliberada de payload | Cadastro/login, hashes, ausência de senha/segredo |
| 3 | F-001, F-002, F-003 | T02/T09 — bloquear SQL arbitrário, parametrizar e autorizar | admin, repositories, rotas | Mudança deliberada de segurança no contrato | Testes de injection e matriz `401/403` |
| 4 | F-006, F-007, F-008 | T05/T06 — ciclo de conexão, transação e invariantes | `database.py`, repositories, domínio | Compatibilidade com banco existente | Rollback por falha, concorrência e integridade |
| 5 | F-009, F-010 | T03/T04 — separar MVC/casos de uso | `models.py`, `controllers.py`, `app.py`, novos pacotes | Regressão de status/payload | Testes de todos os 19 contratos |
| 6 | F-011, F-012 | T07/T08 — queries em lote e validação única | repositories, domínio, presenters | Alteração da ordem/forma dos dados | Query count e comparação estrutural de payload |
| 7 | F-013, F-015 | T10 — error mapper, logging e higiene | adapters HTTP, bootstrap e módulos existentes | Mudança involuntária de erro público | Matriz de erros e análise estática |
| 8 | Todos | Testes e validação final | novos testes; documentação estritamente necessária | Cobertura inicial inexistente | Sintaxe, testes, boot, contratos, regressão e diff |

Mudanças de contrato que a aprovação do plano precisa autorizar explicitamente:

- `/admin/query` deixará de executar SQL arbitrário; a rota será mantida apenas como operação administrativa fechada ou resposta de descontinuação segura.
- Rotas administrativas, leitura de usuários e operações mutáveis passarão a aceitar `401/403`.
- Login poderá adicionar um token ao envelope existente.
- Respostas de usuário deixarão de conter o campo de senha.
- `/health` deixará de expor segredo, debug e path interno.
- Métodos, paths e envelopes de sucesso das demais operações serão preservados.

## Expected MVC Target

```text
app.py                         # composition root e boot
config.py                      # configuração externa

store/
├── domain/
│   ├── models.py              # Produto, Usuário, Pedido e invariantes
│   ├── policies.py            # status, categorias e regras
│   └── errors.py              # erros de domínio
├── controllers/
│   ├── products.py            # casos de uso de produtos
│   ├── users.py               # cadastro e autenticação
│   ├── orders.py              # pedidos, estoque e status
│   └── reports.py             # relatório de vendas
├── views/
│   ├── routes.py              # adapters HTTP/registro de rotas
│   ├── serializers.py         # DTOs públicos
│   └── error_mapper.py        # domínio → HTTP
└── infrastructure/
    ├── sqlite.py              # conexão, schema e transações
    └── repositories.py        # queries parametrizadas

tests/
├── unit/
├── integration/
└── contracts/
```

Direção pretendida:

```text
HTTP/View adapter → Controller/use case → Domain model/policy
                                      → Repository interface
Infrastructure SQLite implements repository interfaces
app.py compõe dependências; domínio não importa Flask nem sqlite3
```

## Risks and Preconditions

- A pasta `.codex/` não rastreada deve ser preservada.
- Não existe suíte de regressão; o baseline inicial dependerá de contract tests criados antes da reorganização.
- `loja.db` contém dados gerados e não será usado diretamente em testes; baseline e migrations usarão cópia ou banco temporário.
- Senhas existentes exigem estratégia de migração para hash.
- Chaves reais não serão criadas nem armazenadas; boot de teste usará segredo efêmero.
- O runtime mínimo precisa ser declarado.
- Mudanças de segurança listadas acima alteram contratos inseguros e dependem da aprovação explícita.
- Build, testes e boot ainda não foram executados; não há afirmação de que o baseline atual funciona.

## Human Gate

Phase 2 foi concluída com a codebase em modo somente-leitura e este relatório foi salvo em `reports/audit-project-1.md` antes do checkpoint. A Fase 3 foi autorizada e executada em um turno posterior.

**Checkpoint apresentado:** `Phase 2 complete. Autoriza executar a Fase 3 e modificar os arquivos conforme o plano apresentado? [y/n]`

**Checkpoint status:** `APPROVED`

## Phase 3 Results

**Status:** `COMPLETE`

### Changes

- **Report saved at:** `reports/audit-project-1.md`
- **Changed files:** `README.md`, `app.py`, `config.py`, `controllers.py`, `database.py`, `models.py`, `requirements.txt`, `store/**` e `tests/**`.
- **New architecture:** adapters HTTP em `store/views`, casos de uso em `store/controllers`, domínio e ports em `store/domain`, persistência/segurança em `store/infrastructure` e `app.py` como composition root.
- **Resolved findings:** F-001 a F-015.
- **Residual findings/risks:** nenhum `CRITICAL` ou `HIGH`; não há linter/type checker dedicado configurado.

### Validation Evidence

| Check | Command/method | Result | Evidence |
|---|---|---|---|
| Restore/build/load | `.venv/bin/python -m pip check` e import configurado | PASS | dependências íntegras; import não cria banco; segredo ausente falha claramente |
| Static analysis/types/lint | `python -m compileall -q` + busca arquitetural | PASS | sintaxe válida; domínio não importa Flask/SQLite e Views não executam SQL |
| Automated tests | `python -m unittest discover -s tests -v` | PASS | 13/13 testes, também com warnings tratados como erro |
| Unit boot/readiness | servidor HTTP em porta temporária | PASS | readiness real e encerramento limpo |
| Public contracts | contract tests e 20 requisições HTTP reais | PASS | 19 métodos/paths preservados; correções de segurança autorizadas cobertas |
| Regression audit | varredura dirigida F-001–F-015 | PASS | todos os findings resolvidos; nenhuma regressão crítica/alta encontrada |
| Scope/diff | `git diff --check -- code-smells-project` | PASS | sem erros de whitespace nem resíduos temporários; `loja.db` original preservado |

### Contract Comparison

| Type | Identity | Before | After | Result |
|---|---|---|---|---|
| HTTP | 19 operações inventariadas | métodos, paths e shapes inseguros originais | métodos/paths preservados; autenticação/DTOs seguros e `/admin/query` desativado com `410` | PASS — mudanças de segurança aprovadas |

### Final Status

`COMPLETE`
