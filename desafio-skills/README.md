# Desafio: Skill `refactor-arch` — Auditoria e refatoração MVC

Entrega do desafio de Skills para refatoração arquitetural automatizada. Os três projetos legados estão nesta pasta; o enunciado original está em [ENUNCIADO.md](ENUNCIADO.md).

## A) Análise Manual

Para cada projeto foram identificados **pelo menos cinco** problemas, com **pelo menos um CRITICAL ou HIGH**, **dois MEDIUM** e **dois LOW**, com foco em impacto arquitetural, segurança e manutenção.

### `code-smells-project` (Python / Flask — e-commerce)

| # | Severidade | Problema | Onde | Por que importa |
|---|------------|----------|------|-----------------|
| 1 | **CRITICAL** | **SQL injection** por concatenação de strings em queries (`SELECT`, `INSERT`, `UPDATE`, login) | `models.py` (ex.: linhas 28, 47–49, 110, 127–128, 140+) | Permite exfiltração ou destruição de dados; viola qualquer baseline de segurança. |
| 2 | **CRITICAL** | **Endpoint administrativo `/admin/query`** executa SQL arbitrário enviado pelo cliente | `app.py` ~59–78 | Backdoor equivalente: compromete o banco inteiro. |
| 3 | **HIGH** | **Credenciais e configuração sensível** (`SECRET_KEY` fixo, `DEBUG=True`) e **vazamento no `/health`** (`secret_key` no JSON) | `app.py` 7–8; `controllers.py` 264–290 | Exposição de segredos e superfície de ataque; health não deve vazar chaves. |
| 4 | **MEDIUM** | **Acoplamento e “God module”**: `models.py` concentra persistência, regras e montagem de resposta; validação de negócio repetida em `controllers.py` | `models.py`, `controllers.py` | Dificulta testes unitários e evolução por domínio. |
| 5 | **MEDIUM** | **Lista de usuários retorna `senha` em claro** para clientes da API | `models.py` `get_todos_usuarios` / serialização | Violação de privacidade e incentiva abuso se vazamento de logs. |
| 6 | **LOW** | **Mensagens de negócio simuladas** (`print` de e-mail/SMS) misturadas ao fluxo HTTP | `controllers.py` 207–210 | Ruído operacional; ideal extrair para serviço de notificação ou fila. |
| 7 | **LOW** | **`DEBUG=True` como padrão em produção** e magic numbers nas faixas do relatório de faturamento | `app.py` 9; `models.py` 256–262 | Flag de debug ativa stack trace ao cliente; constantes sem nome dificultam ajuste de regras de negócio. |

### `ecommerce-api-legacy` (Node.js / Express — LMS + checkout)

| # | Severidade | Problema | Onde | Por que importa |
|---|------------|----------|------|-----------------|
| 1 | **CRITICAL** | **Segredos hardcoded** (gateway, SMTP, DB) em `config` no código-fonte | `utils.js` 1–7 | Compromete produção e auditoria; credenciais no repositório. |
| 2 | **HIGH** | **God Class**: `AppManager` inicializa DB, define rotas e orquestra checkout e relatórios | `AppManager.js` | MVC inexistente; impossível testar ou substituir camadas. |
| 3 | **HIGH** | **“Crypto” customizado fraco** (`badCrypto`) para senhas | `utils.js` 17–23 | Não é KDF adequado; facilita abuso offline se o DB vazar. |
| 4 | **MEDIUM** | **Callback hell / fluxo assíncrono aninhado** no checkout e no relatório financeiro | `AppManager.js` 37–77, 80–128 | Bugs de concorrência e manutenção; erros difíceis de raciocinar. |
| 5 | **MEDIUM** | **Padrão N+1** no relatório (`forEach` de cursos → queries por matrícula/usuário/pagamento) | `AppManager.js` 89–126 | Degrada com volume; sintoma de ausência de camada de acesso a dados. |
| 6 | **LOW** | **Variáveis de uma letra** (`u`, `e`, `p`, `cid`, `cc`) em API pública | `AppManager.js` 28–33 | Legibilidade e revisão de segurança piores. |
| 7 | **LOW** | **`console.log` de dados sensíveis** em produção (`cardNumber`, chave de gateway) | `AppManager.js` 45 | PII/PCI em logs; impossibilita compliance sem rotação emergencial. |

### `task-manager-api` (Python / Flask + SQLAlchemy — Task Manager)

| # | Severidade | Problema | Onde | Por que importa |
|---|------------|----------|------|-----------------|
| 1 | **CRITICAL** | **Credenciais SMTP hardcoded** (`email_password`) | `services/notification_service.py` 9–10 | Vazamento de segredo; bloqueia rotação segura. |
| 2 | **HIGH** | **`User.to_dict()` expõe hash/senha** no payload JSON | `models/user.py` 16–25 | Qualquer cliente que liste usuários vê material para ataque offline. |
| 3 | **HIGH** | **Hash MD5 para senhas** | `models/user.py` 27–32 | Algoritmo inadequado para credenciais; não segue práticas atuais. |
| 4 | **MEDIUM** | **N+1 queries** ao montar lista de tasks (busca `User` e `Category` por item) | `routes/task_routes.py` 11–57 | Latência cresce linearmente com número de tasks. |
| 5 | **MEDIUM** | **Lógica de apresentação e regras** (overdue, montagem de dict) na camada de rotas | `routes/task_routes.py`, `routes/user_routes.py` | Dificulta reuso e testes; mistura responsabilidades de controller/view. |
| 6 | **LOW** | **`except:` sem tipo** e retorno genérico de erro | `task_routes.py` 62–63, 236–237 | Esconde falhas reais e dificulta observabilidade. |
| 7 | **LOW** | **Token JWT fictício** (`fake-jwt-token-<id>`) retornado no login sem assinatura | `routes/user_routes.py` 207–211 | Falsa sensação de segurança; clientes assumem JWT real e não validam expiração/assinatura. |

---

## B) Construção da Skill

A skill **`refactor-arch`** está em **Markdown**, compatível com [Claude Code Skills](https://code.claude.com/docs/en/skills) e com [progressive disclosure](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), em:

- [code-smells-project/.claude/skills/refactor-arch/](code-smells-project/.claude/skills/refactor-arch/) (cópia idêntica em `ecommerce-api-legacy` e `task-manager-api`)

**Arquivos:**

| Arquivo | Papel |
|---------|--------|
| `SKILL.md` | Fases 1–3, gate humano antes da Fase 3, `disable-model-invocation: true` |
| `project-analysis-heuristics.md` | Detecção de stack, DB, contagem de fontes, ramificações Python/Node |
| `anti-patterns-catalog.md` | ≥8 anti-patterns + bloco “APIs deprecated” |
| `audit-report-template.md` | Formato do relatório (CRITICAL → LOW, arquivo:linhas) |
| `mvc-guidelines.md` | Model / View / Controller, config, errors |
| `refactoring-playbook.md` | ≥8 transformações com antes/depois |

**Decisões de design**

- **`disable-model-invocation: true`:** a skill é um fluxo com efeitos colaterais e confirmação obrigatória; só deve rodar com `/refactor-arch`.
- **Catálogo + playbook paralelos:** o primeiro detecta; o segundo guia a correção sem acoplar a um único framework.
- **Deprecated APIs:** item explícito no catálogo com saída “N/A” quando nada for encontrado, para não forçar achados falsos.

**Desafios**

- Projetos com níveis diferentes de organização exigiram playbook com padrões incrementais (ex.: extrair serviços antes de criar pastas novas).
- No Windows, validação automatizada precisou de `pip install --user` em um ambiente onde `Scripts/` estava com permissões restritivas.

---

## C) Resultados

### Relatórios de auditoria (Fase 2)

- [reports/audit-project-1.md](reports/audit-project-1.md) — `code-smells-project`
- [reports/audit-project-2.md](reports/audit-project-2.md) — `ecommerce-api-legacy`
- [reports/audit-project-3.md](reports/audit-project-3.md) — `task-manager-api`

Cada relatório contém **≥ 5 findings**, com **≥ 1 CRITICAL ou HIGH**, ordenados por severidade, com caminhos e linhas **referentes ao código legado** antes da Fase 3.

### Resumo por severidade (conteúdo dos relatórios)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW |
|---------|----------|------|--------|-----|
| code-smells-project | 3 | 2 | 2 | 1 |
| ecommerce-api-legacy | 1 | 3 | 2 | 1 |
| task-manager-api | 1 | 2 | 3 | 2 |

### Antes / depois (estrutura)

**Projeto 1 —** de `app.py` + `controllers.py` + `models.py` + `database.py` para `app.py` + `src/config/`, `src/database.py`, `src/repositories/`, `src/views/routes.py`, `src/middleware/errors.py`. Removido `/admin/query`; reset protegido por `ENABLE_ADMIN_RESET`.

**Projeto 2 —** de `AppManager.js` + `utils.js` para `src/config.js`, `src/database.js`, `src/password.js`, `src/cache.js`, `src/services/*`, `src/routes.js`, `src/app.js` assíncrono.

**Projeto 3 —** mantidos `models/` e `routes/`, adicionado `controllers/task_controller.py`; `config.py` para env; `User` com Werkzeug; `NotificationService` sem segredos no fonte.

### Validação local (logs)

Testes executados em 2026-05-13 (Windows 10, Python 3.12, Node.js 20):

```text
# code-smells-project — porta 5000
GET /health  → 200 | {"status":"ok","database":"connected","counts":{"produtos":10,"usuarios":3,"pedidos":0},"versao":"1.0.0"}
GET /produtos → 200 | 10 produtos retornados
GET /usuarios → 200 | 3 usuários retornados

# ecommerce-api-legacy — porta 3000
GET /api/admin/financial-report → 200 | {"value":[{"course":"Clean Architecture","revenue":997},{"course":"Docker","revenue":0}],"Count":2}
POST /api/checkout              → 200 | {"msg":"Sucesso","enrollment_id":2}

# task-manager-api — porta 5000
GET  /health                        → 200 | {"status":"ok","timestamp":"2026-05-13 22:45:02"}
POST /users                         → 201 | usuário criado com hash Werkzeug
POST /tasks (priority: 2, int)      → 201 | task criada com user_name resolvido via joinedload
POST /tasks (priority: "high", str) → 400 | {"error":"Prioridade deve ser um inteiro entre 1 e 5"} (fix aplicado)
GET  /tasks                         → 200 | lista com campo "overdue" calculado
```

### Checklist de validação

#### `code-smells-project`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: Python
- [x] Framework detectado corretamente: Flask 3.x
- [x] Domínio descrito corretamente: API de e-commerce (produtos, usuários, pedidos)
- [x] Número de arquivos analisados: 4 (app.py, controllers.py, models.py, database.py)

**Fase 2 — Auditoria**
- [x] Relatório segue o template (blocos `===`, Summary, Findings)
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados CRITICAL → HIGH → MEDIUM → LOW
- [x] Mínimo de 5 findings: 8 encontrados (CRITICAL:3, HIGH:2, MEDIUM:2, LOW:1)
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()` — N/A no legado)
- [x] Skill pausa e pede confirmação antes da Fase 3 (gate em `SKILL.md`)

**Fase 3 — Refatoração**
- [x] Estrutura MVC: `src/config/`, `src/repositories/`, `src/views/`, `src/middleware/`
- [x] Configuração em `src/config/settings.py` via `os.environ`; sem hardcoded
- [x] Models/Repositories: `src/repositories/products.py`, `users.py`, `orders.py`
- [x] Views/Routes: `src/views/routes.py` (Blueprints)
- [x] Controllers: lógica de negócio nos repositories (sem SQL inline nas rotas)
- [x] Error handling: `src/middleware/errors.py` com `@app.errorhandler`
- [x] Entry point claro: `app.py` (composition root)
- [x] Aplicação inicia sem erros: `GET /health → 200`
- [x] Endpoints originais respondem: `/health`, `/produtos`, `/usuarios` → 200

---

#### `ecommerce-api-legacy`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: JavaScript (Node.js)
- [x] Framework detectado corretamente: Express 4.x
- [x] Domínio descrito corretamente: LMS com checkout de cursos e relatório financeiro
- [x] Número de arquivos analisados: 3 principais (AppManager.js, utils.js, app.js)

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados CRITICAL → HIGH → MEDIUM → LOW
- [x] Mínimo de 5 findings: 8 encontrados (CRITICAL:1, HIGH:3, MEDIUM:3, LOW:1)
- [x] Detecção de APIs deprecated incluída (N/A — `req.param()` e `new Buffer()` não encontrados)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC: `src/config.js`, `src/database.js`, `src/services/`, `src/routes.js`
- [x] Configuração via `process.env`; sem segredos hardcoded
- [x] Models: `src/database.js` com wrappers Promise (`dbGet`, `dbRun`, `dbAll`)
- [x] Views/Routes: `src/routes.js` com handlers finos
- [x] Controllers (serviços): `CheckoutService`, `ReportService`, `UserService`
- [x] Error handling: middleware `(err, req, res, next)` em `src/app.js`
- [x] Entry point claro: `src/app.js` (factory `buildApp`)
- [x] Aplicação inicia sem erros: `Frankenstein LMS rodando na porta 3000`
- [x] Endpoints originais respondem: `/api/admin/financial-report` e `/api/checkout` → 200

---

#### `task-manager-api`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: Python
- [x] Framework detectado corretamente: Flask + SQLAlchemy
- [x] Domínio descrito corretamente: Task Manager (usuários, tasks, categorias)
- [x] Número de arquivos analisados: ~15 arquivos fonte

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados CRITICAL → HIGH → MEDIUM → LOW
- [x] Mínimo de 5 findings: 8 encontrados (CRITICAL:1, HIGH:2, MEDIUM:3, LOW:2)
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()` — MEDIUM)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC: `config.py`, `models/`, `routes/`, `controllers/`, `services/`
- [x] Configuração em `config.py` via `python-dotenv`; sem hardcoded
- [x] Models: `models/user.py` com Werkzeug hash; `models/task.py`, `models/category.py`
- [x] Views/Routes: `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- [x] Controllers: `controllers/task_controller.py` com `joinedload` e validações tipadas
- [x] Error handling: handlers de exceção nos blueprints
- [x] Entry point claro: `app.py` com `db.create_all()`
- [x] Aplicação inicia sem erros: `GET /health → 200`
- [x] Endpoints originais respondem: `/health`, `/tasks`, `/users` → 200

---

## D) Como executar

### Pré-requisitos

- [Claude Code](https://code.claude.com/docs/en/overview) instalado e autenticado (`claude` no PATH).
- **Python 3.10+** e **Node.js 18+**.
- Dependências: `pip install -r requirements.txt` / `npm install` em cada projeto.

### Invocar a skill (exemplo)

```powershell
Set-Location desafio-skills\code-smells-project
claude "/refactor-arch"
```

Repita em `desafio-skills\ecommerce-api-legacy` e `desafio-skills\task-manager-api`.

### Subir os projetos após refatoração

**code-smells-project**

```powershell
Set-Location desafio-skills\code-smells-project
python -m pip install -r requirements.txt
python app.py
```

Variáveis úteis: `SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`, `ENABLE_ADMIN_RESET=true` (somente dev).

**ecommerce-api-legacy**

```powershell
Set-Location desafio-skills\ecommerce-api-legacy
npm install
npm start
```

Opcional: `PAYMENT_GATEWAY_KEY`, `PORT`.

**task-manager-api**

```powershell
Set-Location desafio-skills\task-manager-api
python -m pip install -r requirements.txt
python app.py
```

Opcional: arquivo `.env` com `SECRET_KEY`, `DATABASE_URL`, `SMTP_*`.

### Smoke tests sugeridos

- `GET http://localhost:5000/health` (projetos Flask na porta padrão do `app.py`).
- `GET http://localhost:3000/api/admin/financial-report` (Express).
- Exercitar `ecommerce-api-legacy/api.http` no REST Client do VS Code.
