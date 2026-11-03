# Desafio — Skill `refactor-arch` (Refatoração Arquitetural Automatizada)

Skill do **Claude Code** que analisa, audita e refatora projetos backend legados para o padrão **MVC**, de forma agnóstica de tecnologia. Ela foi executada nos 3 projetos do repositório (2× Python/Flask, 1× Node.js/Express).

| Entregável | Local |
|---|---|
| Skill (SKILL.md + 5 referências) | `*/.claude/skills/refactor-arch/` (cópias idênticas nos 3 projetos) |
| Relatórios de auditoria (Fase 2) | [reports/audit-project-1.md](reports/audit-project-1.md), [reports/audit-project-2.md](reports/audit-project-2.md), [reports/audit-project-3.md](reports/audit-project-3.md) |
| Código refatorado (Fase 3) | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |

---

## A) Análise Manual

Problemas identificados lendo o código **antes** de escrever a skill. A lista completa, com linhas exatas, está nos relatórios. Aqui ficam os achados mais relevantes e a justificativa de cada um.

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection em praticamente todas as queries (concatenação de strings) | `models.py:28, 47-50, 109-111, 289-299…` | O login aceita `' OR '1'='1' --`; dá para ler e apagar qualquer tabela. |
| CRITICAL | Endpoint `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga o banco, os dois sem autenticação | `app.py:47-78` | Qualquer pessoa na rede destrói ou exfiltra a base com uma requisição. |
| CRITICAL | Senhas em texto puro, devolvidas por `GET /usuarios`; `/health` expõe a `secret_key` | `models.py:83, 99`; `controllers.py:285-289` | Vazamento direto de credenciais para clientes anônimos. |
| CRITICAL | God File: `models.py` mistura SQL, regras e formatação de 4 domínios | `models.py:1-314` | Não dá para testar nada isoladamente, e toda mudança tem efeito colateral. |
| HIGH | Conexão SQLite global e mutável (`global db_connection`, `check_same_thread=False`) | `database.py:4-11` | Requests compartilham a mesma transação, o que gera corrida e commits parciais. |
| MEDIUM | N+1 na listagem de pedidos (1 query por pedido + 1 por item) | `models.py:171-233` | A latência cresce linearmente com o volume. |
| MEDIUM | Validação ausente: body vazio gera 500; quantidade negativa no pedido aumenta o estoque | `controllers.py:169-170, 195-201` | Erros 500 e brecha de fraude de estoque/valor. |
| LOW | Magic numbers nas faixas de desconto (`10000`, `0.1`…) | `models.py:256-262` | Regra de negócio escondida. |
| LOW | `print` como log, incluindo e-mails de usuários | `controllers.py:179, 182, 208-210…` | Log sem nível e com PII. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | God Class `AppManager`: banco, seed, rotas, SQL e regra de pagamento numa classe só | `src/AppManager.js:4-139` | Acoplamento total; impossível trocar banco ou gateway. |
| CRITICAL | Senha de banco de produção e chave `pk_live_` do gateway hardcoded | `src/utils.js:1-7` | Segredos vazam pelo repositório. |
| CRITICAL | Número completo do cartão + chave do gateway impressos no log | `src/AppManager.js:45` | Violação de PCI-DSS. |
| CRITICAL | "Hash" de senha caseiro (base64 truncado) e senha padrão `123456` | `src/utils.js:17-23`, `src/AppManager.js:68` | Senhas reversíveis ou conhecidas. |
| HIGH | Callback hell de 5 níveis sem transação no checkout | `src/AppManager.js:37-77` | Uma falha no meio deixa matrícula sem pagamento ou usuário órfão. |
| MEDIUM | N+1 no relatório financeiro, sincronizado por contadores manuais | `src/AppManager.js:83-128` | 1 + C + 2·E queries; e um erro no meio derruba o processo (`enrollments.length` de `undefined`). |
| MEDIUM | `DELETE /api/users/:id` deixa matrículas e pagamentos órfãos | `src/AppManager.js:131-137` | Inconsistência de dados financeiros. |
| LOW | Nomes crípticos (`u`, `e`, `p`, `cc`, `cid`, `badCrypto`) | `src/AppManager.js:29-33` | Intenção obscura. |
| LOW | Código morto (`totalRevenue`, `dbUser`, `smtpUser`) | `src/utils.js:2-10, 25` | Ruído e falsa funcionalidade. |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager parcialmente organizado)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | MD5 sem salt para senhas, e o hash é devolvido em `to_dict()` | `models/user.py:16-32` | O hash MD5 exposto é revertido em segundos. |
| CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Credenciais versionadas. |
| HIGH | Token falso `'fake-jwt-token-' + id`; qualquer cliente cria usuário `admin` | `routes/user_routes.py:52, 210` | Tokens forjáveis e escalonamento de privilégio. |
| HIGH | Rotas gordas com regra de negócio (relatório de 90 linhas); service nunca usado; sem controllers | `routes/report_routes.py:12-101`, `services/notification_service.py` | As camadas existem, mas não cumprem seu papel. |
| MEDIUM | APIs deprecated: `datetime.utcnow()` (22×) e `Query.get()` (16×) | `models/*.py`, `routes/*.py`, `seed.py` | Warnings hoje e quebra em versões futuras. |
| MEDIUM | N+1 em `GET /tasks` (2 queries por task) e nos relatórios | `routes/task_routes.py:41-57` | Performance degrada com os dados. |
| MEDIUM | Regra "task atrasada" duplicada 6×, mesmo existindo `Task.is_overdue()` | `routes/*.py` | Risco de divergência. |
| LOW | 20 imports não usados e `utils/helpers.py` inteiro sem uso | vários | Ruído e dependências desnecessárias. |
| LOW | `print` como log e `except:` sem tipo | `routes/*.py` | Falhas silenciosas. |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": papel, 3 fases, regras invioláveis, formatos de saída
└── references/
    ├── project-analysis.md               # Fase 1 — heurísticas de linguagem, framework, banco, domínio, arquitetura, endpoints
    ├── anti-patterns-catalog.md          # Fase 2 — 22 anti-patterns com sinais de detecção (grep + estruturais) e severidade
    ├── report-template.md                # Fase 2 — template obrigatório do relatório + exemplos bom/ruim
    ├── mvc-guidelines.md                 # Fase 3 — camadas, regras de dependência, adaptação ao contexto, contrato HTTP
    └── refactoring-playbook.md           # Fase 3 — 20 transformações com código antes/depois (Python e JS)
```

### Decisões de design

- **O SKILL.md orquestra e as referências guardam o conhecimento.** O SKILL.md define *o que* fazer em cada fase e o formato exato de saída. O *como* fica nos arquivos de referência, carregados sob demanda ("leia sempre o arquivo da fase antes de executá-la"). Isso mantém o prompt principal curto (progressive disclosure).
- **Pausa obrigatória**: a Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, e a skill proíbe qualquer escrita no projeto antes do "sim". O único arquivo permitido nessa fase é o relatório.
- **Baseline antes de mudar**: a Fase 1 captura o comportamento real dos endpoints numa cópia temporária do projeto. A Fase 3 compara contra ela status codes **e forma do JSON**.
- **Contrato HTTP é inviolável**, exceto por segurança: toda mudança de contrato (ex.: remover `senha` da resposta) precisa ser listada no resumo final.
- **Rastreabilidade AP → PB**: cada anti-pattern do catálogo aponta para o padrão do playbook que o corrige, e cada finding do relatório cita os dois.
- **Argumento opcional** (`/refactor-arch reports/audit-project-1.md`) para escolher onde salvar o relatório.

### Catálogo de anti-patterns (22) e por quê

| Severidade | Anti-patterns | Motivação |
|---|---|---|
| CRITICAL (6) | SQL Injection, credenciais hardcoded, God Class, exposição de dados sensíveis, endpoint admin sem auth, hash de senha inseguro | Todos foram encontrados na análise manual e permitem comprometimento imediato. |
| HIGH (6) | Fat Controller, estado global mutável, ausência de DI, multi-etapa sem transação/callback hell, auth falsa, debug em produção | Violações fortes de MVC/SOLID citadas no enunciado e presentes nos 3 projetos. |
| MEDIUM (6) | N+1, validação ausente/duplicada, tratamento de erros, código duplicado, integridade referencial, **APIs deprecated** | Problemas de performance/padronização. A seção de deprecated traz uma tabela por stack (Python, SQLAlchemy, Flask, Node, Express) com o substituto moderno. |
| LOW (4) | Magic numbers, nomenclatura, imports/código morto, logging com print | Legibilidade. |

Cada entrada tem **sinais acionáveis** (ex.: "query dentro de `for`/`forEach` que itera resultado de outra query", regex de `grep`) em vez de descrições vagas.

### Como a skill é agnóstica de tecnologia

- As heurísticas de detecção cobrem Python, Node/TS, Go, Java, Ruby e PHP, com tabelas de sinais por framework (Flask, Django, FastAPI, Express, NestJS, Spring…).
- Os sinais de detecção e os exemplos do playbook vêm em Python **e** JavaScript.
- `mvc-guidelines.md` traz uma estrutura alvo por stack e uma tabela de **adaptação ao contexto**:
  - monolito em poucos arquivos → criar `src/` com shim no entry point;
  - God Class → desmontar a classe;
  - projeto com camadas parciais → **não mover para `src/`**: manter as pastas existentes e preencher as camadas que faltam.
- As regras de dependência entre camadas são verificáveis por `grep` (ex.: nada de `jsonify`/`request` em `controllers/`).

### Desafios encontrados e soluções

| Desafio | Solução |
|---|---|
| A porta 5000 é ocupada pelo AirPlay no macOS e as apps tinham porta fixa | Porta via `PORT` na config; a skill manda checar com `lsof` antes do boot. |
| Trocar `datetime.utcnow()` por `datetime.now(timezone.utc)` quebra comparações com datas *naive* do SQLite | Helper `utcnow()` que devolve UTC naive (documentado no PB-17). |
| Corrigir segurança sem quebrar clientes (senha em texto puro/MD5 em bancos existentes) | Migração transparente: hashes legados são convertidos no boot (projeto 1) ou no primeiro login (projeto 3). |
| SQLite em memória com conexão única no Node não aceita transações concorrentes | `Database.transaction()` com fila de promessas; testado com 10 checkouts paralelos. |
| Os comandos `grep --include=*.py` falharam no zsh, e `print\(` casava com `Blueprint(` | 2ª iteração da skill: globs entre aspas, `\bprint\(` e uma seção "Armadilhas conhecidas" no SKILL.md. |
| Garantir que "endpoint responde" significa "mesmo contrato" | A skill passou a exigir comparação da forma do JSON (chaves/tipos) com a baseline. |

---

## C) Resultados

### Resumo das auditorias

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 | 6 | 5 | 4 | 3 | **18** |
| 2 — ecommerce-api-legacy | Node.js + Express 4.22.1 | 5 | 4 | 5 | 4 | **18** |
| 3 — task-manager-api | Python + Flask 3.0.0 | 3 | 4 | 6 | 4 | **17** |

### Antes × depois

**Projeto 1** — monolito em 4 arquivos → `src/` em camadas

```
ANTES                         DEPOIS
app.py  (rotas+SQL+config)    app.py                      # shim → src.app.create_app()
controllers.py                src/app.py                  # composition root (DI)
models.py (4 domínios)        src/config/settings.py
database.py (global)          src/database/{connection,schema}.py
                              src/models/{produto,usuario,pedido,admin}_model.py
                              src/controllers/{produto,usuario,pedido,sistema}_controller.py
                              src/views/{produto,usuario,pedido,sistema}_routes.py
                              src/validators/  src/services/notification_service.py
                              src/middlewares/{error_handler,auth}.py  src/utils/errors.py
```

**Projeto 2** — God Class → MVC em `src/`

```
ANTES                         DEPOIS
src/app.js                    src/app.js                  # composition root (createApp)
src/AppManager.js (tudo)      src/config/index.js
src/utils.js (config+cache)   src/database/{connection,schema}.js   # async + transações
                              src/models/{user,course,enrollment}Model.js
                              src/services/{payment,password,cache}Service.js
                              src/controllers/{checkout,report,user}Controller.js
                              src/views/routes.js
                              src/middlewares/{asyncHandler,errorHandler,requireAdmin}.js
                              src/utils/{errors,logger}.js
```

**Projeto 3** — camadas parciais → camadas completas (mantendo o layout na raiz)

```
ANTES                         DEPOIS
app.py (config hardcoded)     app.py                      # create_app() + composition root
models/ (MD5, to_dict c/ senha) models/                   # regras, consultas sem N+1, serialização segura
routes/ (regra de negócio)    routes/                     # views finas + category_routes, system_routes
services/ (nunca usado)       services/{notification,token}_service.py  # injetados
utils/helpers.py (sem uso)    utils/{clock,errors}.py
—                             config/  controllers/  validators/  middlewares/
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.22.1 | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS + checkout | ✅ Task Manager |
| Número de arquivos condiz com a realidade | ✅ 4 (780 linhas) | ✅ 3 (180 linhas) | ✅ 13 (1158 linhas) |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 18 | ✅ 18 | ✅ 17 |
| Detecção de APIs deprecated | ✅ (nenhuma, declarado) | ✅ (nenhuma, declarado) | ✅ `utcnow`, `Query.get` |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/` | ✅ `src/views/routes.js` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ (inclusive com `-W error::DeprecationWarning`) |
| Endpoints originais respondem corretamente | ✅ 19/19 | ✅ 3/3 | ✅ 22/22 |

### Logs de validação (após a refatoração)

<details>
<summary>Projeto 1 — boot + 35 requisições HTTP (trecho)</summary>

```
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5051
GET /health 200 {"ambiente": "development", "counts": {"pedidos": 0, "produtos": 10, "usuarios": 3}, "database": "connected", "status": "ok", "versao": "1.0.0"}
GET /usuarios/1 200 {"dados": {"criado_em": "...", "email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, "sucesso": true}
POST /login 200 {"dados": {"email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, "mensagem": "Login OK", "sucesso": true}
POST /login 401 {"erro": "Email ou senha inválidos", "sucesso": false}        # payload ' OR '1'='1' --
POST /pedidos 201 {"dados": {"pedido_id": 1, "total": 6179.79}, ...}
POST /pedidos 400 {"erro": "Item inválido: produto_id e quantidade (> 0) são obrigatórios", ...}   # quantidade -5
GET /relatorios/vendas 200 {"dados": {"desconto_aplicavel": 308.99, "faturamento_bruto": 6179.79, ...}}  # idêntico ao original
POST /admin/query 401 {"erro": "Token administrativo inválido", "sucesso": false}
POST /admin/query 400 {"erro": "Apenas consultas SELECT são permitidas", "sucesso": false}
WARNING src.database.schema: 4 senha(s) legada(s) em texto puro migrada(s) para hash   # boot com banco antigo
```
</details>

<details>
<summary>Projeto 2 — boot + requisições do api.http + concorrência</summary>

```
INFO LMS API rodando na porta 3001
POST /api/checkout -> {"msg":"Sucesso","enrollment_id":2} [200]
POST /api/checkout -> Pagamento recusado [400]
POST /api/checkout -> Curso não encontrado [404]
POST /api/checkout -> Bad Request [400]
GET /api/admin/financial-report -> Token administrativo inválido [401]
GET /api/admin/financial-report -> [{"course":"Clean Architecture","revenue":997,...},{"course":"Docker","revenue":994,...}] [200]   # idêntico ao original
DELETE /api/users/1 -> Usuário deletado, junto com suas matrículas e pagamentos. [200]
INFO Processando pagamento de 497 no cartão **** **** **** 4444      # antes: número completo + pk_live
10 checkouts concorrentes: 200 200 200 200 200 200 200 200 200 200
```
</details>

<details>
<summary>Projeto 3 — 27 requisições comparadas com a baseline</summary>

```
Seed concluído com sucesso!  (executado com -W error::DeprecationWarning)
OK  GET /tasks 200 => GET /tasks 200
OK  POST /tasks 201 => POST /tasks 201
OK  GET /reports/summary 200 => GET /reports/summary 200
... 27/27 status codes idênticos
Diferença de forma do JSON: apenas o campo "password" removido de /users/<id>, POST/PUT /users e /login (intencional)
POST /tasks 400 {"error": "Prioridade deve ser entre 1 e 5"}       # antes: 500 com priority "2"
GET /tasks/search?priority=abc 400 {"error": "Prioridade inválida"} # antes: 500
INFO services.notification_service: E-mail (simulado) para maria@email.com: Nova task atribuída
```
</details>

### Mudanças de contrato (todas motivadas por segurança)

- **P1**: `senha` removida de `/usuarios`; `secret_key`/`debug`/`db_path` removidos de `/health`; `/admin/*` exige `X-Admin-Token` (desabilitado sem `ADMIN_TOKEN`); `/admin/query` aceita só um `SELECT` em conexão read-only; status de pedido inexistente retorna 404.
- **P2**: `/api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token`; checkout de usuário novo sem `pwd` retorna 400 (antes: senha `123456`); cartão precisa ter 13–19 dígitos.
- **P3**: `password` removido das respostas; `token` do login agora é assinado (mesmo campo).

### Observações sobre stacks diferentes

- **Monolito Flask (P1)**: a transformação foi a mais profunda (`src/` + shim). O desafio foi preservar o envelope `{"dados", "sucesso"}` e as mensagens exatas de validação, o que se resolveu com validators que repetem a ordem original das checagens.
- **Express (P2)**: a skill aplicou PB-10 (callback → async/await + transação), que não existe nos projetos Python. O formato de erro em texto puro foi mantido no error handler para não quebrar clientes.
- **Flask com camadas parciais (P3)**: graças à tabela de adaptação, a skill **não** moveu tudo para `src/`. Ela preencheu as camadas que faltavam (controllers, config, validators, middlewares) e manteve `seed.py` funcionando (`from app import app, db`).
- **Finding parcialmente tratado**: em P3, a autorização por papel nos endpoints (F-04) ficou como recomendação. Exigir token em todas as rotas quebraria o contrato atual. O token agora é assinado e o `TokenService.verify` está pronto para um guard futuro.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`)
- Python 3.10+ e `pip`; Node.js 18+ e `npm`

### Executar a skill em cada projeto

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch reports/audit-project-1.md"   # ou apenas /refactor-arch

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill imprime a Fase 1, gera e salva o relatório da Fase 2 e **pausa** com `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. Para rodar de novo sobre o código original, use `git checkout 6d1ce62 -- <projeto>`.

### Validar a refatoração manualmente

```bash
# Projeto 1 (porta 5000 ocupada no macOS? use PORT)
cd code-smells-project && pip install -r requirements.txt
PORT=5051 ADMIN_TOKEN=tok python app.py
curl localhost:5051/health
curl localhost:5051/produtos/busca?q=Mouse
curl -X POST -H 'Content-Type: application/json' -d '{"email":"admin@loja.com","senha":"admin123"}' localhost:5051/login

# Projeto 2
cd ecommerce-api-legacy && npm install
ADMIN_TOKEN=troque-este-token npm start      # depois use as requisições de api.http

# Projeto 3
cd task-manager-api && pip install -r requirements.txt
python seed.py && PORT=5053 python app.py
curl localhost:5053/tasks
curl localhost:5053/reports/summary
```

O que verificar: a aplicação sobe sem erros, cada endpoint do inventário (tabelas da Fase 1 nos relatórios) responde com o mesmo status de antes, e os `grep` da seção "Checklist rápido de varredura" do catálogo não retornam mais as ocorrências dos findings.
