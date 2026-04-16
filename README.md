# Skill refactor-arch — Refatoração Arquitetural Automatizada

Skill para Claude Code que analisa, audita e refatora projetos backend para o padrão MVC, de forma agnóstica de tecnologia.

## Análise Manual

### Projeto 1: code-smells-project (Python/Flask — E-commerce API)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **SQL Injection em todas as queries** | CRITICAL | models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 188-224, 280-297 | Todas as queries SQL usam concatenação de strings (`"SELECT * FROM x WHERE id = " + str(id)`). O login (models.py:109-111) permite bypass de autenticação. |
| 2 | **Credenciais hardcoded e dados sensíveis expostos** | CRITICAL | app.py:7-8, database.py:76-84, controllers.py:287-289 | SECRET_KEY `'minha-chave-super-secreta-123'` no código. Health endpoint expõe secret_key, debug mode e db_path. Senhas fracas no seed. |
| 3 | **Senhas armazenadas em texto plano** | CRITICAL | models.py:105-120 | Senhas sem hash no banco. Comparação direta de strings para autenticação. |
| 4 | **Endpoint de execução arbitrária de SQL** | CRITICAL | app.py:59-78 | `/admin/query` aceita e executa qualquer SQL sem autenticação. DROP TABLE, SELECT de dados sensíveis — tudo possível. |
| 5 | **God File — models.py com 314 linhas e 4 domínios** | HIGH | models.py:1-314 | Um único arquivo contém toda lógica de dados para produtos, usuários, pedidos e relatórios. Impossível testar em isolamento. |
| 6 | **N+1 Query Problem** | MEDIUM | models.py:187-200, 219-231 | Loops aninhados com cursor2/cursor3 para buscar itens e nomes de produto por pedido. |
| 7 | **Duplicação de validação** | MEDIUM | controllers.py:30-35, 74-79 | Mesma validação de produto copiada entre criar e atualizar. |
| 8 | **Print-based logging** | LOW | controllers.py:8, 57, 106, 161, 208 | `print()` ao invés de `logging` framework. |
| 9 | **Sem constraints no banco** | LOW | database.py:8-40 | Sem FOREIGN KEY, UNIQUE, NOT NULL ou CHECK constraints. |

### Projeto 2: ecommerce-api-legacy (Node.js/Express — LMS API)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **Credenciais e API keys hardcoded** | CRITICAL | src/utils.js:1-7 | Credenciais de DB, gateway de pagamento, SMTP todas expostas em texto plano no código. |
| 2 | **Password "hashing" com Base64** | CRITICAL | src/utils.js:17-23 | Função `badCrypto()` usa Base64 encoding (reversível) como "criptografia". Não oferece proteção real. |
| 3 | **Secrets logados no console** | CRITICAL | src/AppManager.js:45 | Chave do gateway de pagamento e número de cartão parcialmente logados com `console.log()`. |
| 4 | **Callback Hell (6-7 níveis)** | HIGH | src/AppManager.js:28-78, 80-129 | Callbacks profundamente aninhados no checkout e relatório financeiro. Tratamento de erros inconsistente. |
| 5 | **Sem autenticação em endpoints admin** | HIGH | src/AppManager.js:80, 131 | Relatório financeiro e delete de usuários acessíveis publicamente. |
| 6 | **N+1 queries no relatório** | MEDIUM | src/AppManager.js:80-129 | Queries aninhadas por curso, matrícula, usuário e pagamento. |
| 7 | **Estado global mutável** | MEDIUM | src/utils.js:9-10 | `globalCache = {}` sem TTL ou limites. `totalRevenue` exportado mas nunca usado. |
| 8 | **Validação de pagamento trivial** | MEDIUM | src/AppManager.js:45-46 | Cartão aceito se começa com "4". Sem integração real. |
| 9 | **Nomes de variáveis ilegíveis** | LOW | src/AppManager.js:29-33 | Variáveis `u`, `e`, `p`, `cid`, `cc` ao invés de nomes descritivos. |

### Projeto 3: task-manager-api (Python/Flask — Task Manager)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **Password hashing com MD5** | CRITICAL | models/user.py:29, 32 | MD5 criptograficamente quebrado desde 2004. Senhas reversíveis com rainbow tables em minutos. |
| 2 | **Credenciais hardcoded** | CRITICAL | app.py:13, services/notification_service.py:9-10 | SECRET_KEY e credenciais de email no código. `python-dotenv` nas deps mas não usado para secrets. |
| 3 | **JWT fake sem autenticação real** | CRITICAL | routes/user_routes.py:210 | Token `'fake-jwt-token-' + str(user.id)`. Nenhum endpoint valida tokens. API inteira é pública. |
| 4 | **Hash de senha exposto na API** | HIGH | models/user.py:21, routes/user_routes.py:20-21 | `to_dict()` retorna campo `password`. Combinado com MD5, senhas são reversíveis por qualquer cliente. |
| 5 | **Duplicação massiva de código** | HIGH | routes/task_routes.py:17-28, 30-39 (5 locais) | Lógica overdue duplicada em 5 locais. Conversão task-to-dict duplicada. Validação triplicada. |
| 6 | **Bare except clauses** | MEDIUM | routes/task_routes.py:62, 137, 151, 221, 236; routes/user_routes.py:130, 149 | 11+ locais com `except:` genérico mascarando erros reais. |
| 7 | **N+1 queries** | MEDIUM | routes/task_routes.py:41-48, 50-57 | Query separada por task para buscar usuário e categoria. |
| 8 | **Loops Python para agregação** | MEDIUM | routes/report_routes.py:30-43, 53-68, 119-135 | Carrega tudo na memória para contar. Deveria usar SQL GROUP BY. |
| 9 | **datetime.utcnow() deprecated** | LOW | models/user.py:14, models/task.py:16-17, models/category.py:12 | Deprecated desde Python 3.12. Substituir por `datetime.now(timezone.utc)`. |

---

## Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                       # Prompt principal — define as 3 fases
├── project-analysis.md            # Heurísticas de detecção de stack
├── anti-patterns-catalog.md       # Catálogo de 16 anti-patterns com severidades
├── audit-report-template.md       # Template padronizado do relatório
├── mvc-architecture-guidelines.md # Regras do padrão MVC alvo
└── refactoring-playbook.md        # 10 padrões de transformação com antes/depois
```

### Decisões de Design

**SKILL.md como orquestrador:** O SKILL.md funciona como um prompt que instrui o agente sobre o fluxo das 3 fases sequenciais. Ele referencia os arquivos de conhecimento sem duplicar conteúdo, mantendo cada responsabilidade isolada.

**Catálogo de anti-patterns extenso:** Inclui 16 anti-patterns cobrindo todas as severidades:
- CRITICAL (3): SQL Injection, Hardcoded Credentials, Insecure Password Storage
- HIGH (3): God Class, Missing Authentication, Callback Hell
- MEDIUM (6): N+1 Queries, Code Duplication, Missing Validation, Sensitive Data Exposure, Global Mutable State, Poor Error Handling
- LOW (3): Missing DB Constraints, Magic Numbers, No Pagination
- Bônus: Seção dedicada a APIs deprecated (Python e Node.js)

**Playbook com 10 padrões de transformação:** Cada padrão tem exemplos concretos antes/depois em Python E Node.js, garantindo que a skill funcione em ambas as stacks. Padrões cobrem desde extrair configuração até centralizar error handling.

**Agnosticismo de tecnologia:** Todos os arquivos de referência fornecem exemplos em Python e Node.js. As heurísticas de detecção cobrem ambos os ecossistemas. O template de relatório é genérico.

### Desafios e Soluções

1. **Detecção de stack:** Criado arquivo `project-analysis.md` com tabelas de mapeamento arquivo/import → tecnologia, cobrindo Python, Node.js e outros.
2. **Consistência do relatório:** Template rígido em `audit-report-template.md` com regras de ordenação, mínimos obrigatórios e formato de referência a arquivos.
3. **Pausa obrigatória:** SKILL.md explicita que a Fase 2 DEVE pedir confirmação antes de qualquer modificação, com prompt padronizado.
4. **Adaptação a projetos parcialmente organizados:** O playbook inclui orientações para projetos que já possuem alguma estrutura, focando em melhorias incrementais sem quebrar o que funciona.

---

## Resultados

### Resumo dos Relatórios de Auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|----------|------|--------|-----|-------|
| code-smells-project | 4 | 3 | 4 | 3 | 14 |
| ecommerce-api-legacy | 3 | 3 | 4 | 2 | 12 |
| task-manager-api | 3 | 2 | 5 | 3 | 13 |

### Comparação Antes/Depois

#### Projeto 1: code-smells-project

**Antes:**
```
code-smells-project/
├── app.py          (88 linhas — config + rotas admin + server)
├── controllers.py  (292 linhas — toda lógica de request handling)
├── models.py       (314 linhas — toda lógica de dados, 4 domínios)
└── database.py     (86 linhas — conexão + schema + seed)
```

**Depois (estrutura MVC alvo):**
```
code-smells-project/
├── config/
│   └── settings.py          # Configuração via env vars
├── models/
│   ├── database.py           # Conexão e inicialização
│   ├── product_model.py      # CRUD produtos (queries parametrizadas)
│   ├── user_model.py         # CRUD usuários (bcrypt hashing)
│   └── order_model.py        # CRUD pedidos (com JOINs)
├── controllers/
│   ├── product_controller.py # Lógica de negócio produtos
│   ├── user_controller.py    # Lógica de negócio usuários
│   └── order_controller.py   # Lógica de negócio pedidos
├── views/
│   ├── product_routes.py     # Rotas /produtos
│   ├── user_routes.py        # Rotas /usuários, /login
│   └── order_routes.py       # Rotas /pedidos
├── middlewares/
│   └── error_handler.py      # Error handling centralizado
├── app.py                    # Composition root
└── .env                      # Secrets (gitignored)
```

#### Projeto 2: ecommerce-api-legacy

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js           (14 linhas — setup básico)
├── AppManager.js    (141 linhas — TUDO: DB, rotas, lógica)
└── utils.js         (25 linhas — config, cache, crypto)
```

**Depois (estrutura MVC alvo):**
```
ecommerce-api-legacy/src/
├── config/
│   └── settings.js           # Env vars (dotenv)
├── models/
│   ├── database.js            # Conexão SQLite promisificada
│   ├── userModel.js           # CRUD usuários (bcrypt)
│   ├── courseModel.js          # CRUD cursos
│   └── enrollmentModel.js     # Matrículas + pagamentos
├── controllers/
│   ├── checkoutController.js  # Lógica de checkout
│   └── reportController.js    # Lógica de relatórios
├── routes/
│   ├── checkoutRoutes.js      # POST /api/checkout
│   ├── adminRoutes.js         # GET /api/admin/*
│   └── userRoutes.js          # DELETE /api/users/:id
├── middlewares/
│   └── errorHandler.js        # Error handling centralizado
└── app.js                     # Composition root (async/await)
```

#### Projeto 3: task-manager-api

**Antes:**
```
task-manager-api/
├── app.py           (34 linhas)
├── database.py      (3 linhas)
├── seed.py          (100 linhas)
├── models/          (user.py, task.py, category.py)
├── routes/          (task_routes.py, user_routes.py, report_routes.py)
├── services/        (notification_service.py)
└── utils/           (helpers.py)
```

**Depois (estrutura MVC alvo):**
```
task-manager-api/
├── config/
│   └── settings.py           # Env vars (dotenv)
├── models/
│   ├── database.py            # Init DB
│   ├── user.py                # User model (bcrypt hashing, sem senha no to_dict)
│   ├── task.py                # Task model (métodos utilitários)
│   └── category.py            # Category model
├── controllers/
│   ├── task_controller.py     # Lógica de tarefas
│   ├── user_controller.py     # Lógica de usuários
│   └── report_controller.py   # Lógica de relatórios
├── views/
│   ├── task_routes.py         # Rotas /tasks
│   ├── user_routes.py         # Rotas /users, /login
│   └── report_routes.py       # Rotas /reports, /categories
├── middlewares/
│   └── error_handler.py       # Error handling centralizado
├── services/
│   └── notification_service.py
├── app.py                     # Composition root
└── .env                       # Secrets (gitignored)
```

### Checklist de Validação

#### Projeto 1 — code-smells-project

**Fase 1 — Análise:**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce API)
- [x] Número de arquivos analisados condiz com a realidade (4)

**Fase 2 — Auditoria:**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (14 encontrados)
- [x] Detecção de APIs deprecated incluída
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração:**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Análise:**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS API com checkout)
- [x] Número de arquivos analisados condiz com a realidade (3)

**Fase 2 — Auditoria:**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (12 encontrados)
- [x] Detecção de APIs deprecated incluída
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração:**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 3 — task-manager-api

**Fase 1 — Análise:**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0)
- [x] Domínio da aplicação descrito corretamente (Task Manager API)
- [x] Número de arquivos analisados condiz com a realidade (12)

**Fase 2 — Auditoria:**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (13 encontrados)
- [x] Detecção de APIs deprecated incluída (datetime.utcnow)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração:**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Observações sobre Comportamento em Stacks Diferentes

- **Python/Flask (Projetos 1 e 3):** A skill detecta corretamente Flask via imports e `requirements.txt`. Os padrões de transformação (queries parametrizadas, werkzeug password hashing, Flask blueprints) funcionam diretamente.
- **Node.js/Express (Projeto 2):** A skill detecta Express via `package.json`. A principal diferença é a transformação de callbacks para async/await e o uso de `bcrypt` para Node.js ao invés de `werkzeug`.
- **Projeto parcialmente organizado (Projeto 3):** A skill identifica a estrutura existente e propõe melhorias incrementais — por exemplo, extrair controllers das rotas que já existem e substituir MD5 por bcrypt, sem destruir a organização que já funciona.

---

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e configurado
- Python 3.10+ (para projetos Flask)
- Node.js 18+ (para projeto Express)

### Executar a Skill

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api
cd ../task-manager-api
claude "/refactor-arch"
```

### Validar a Refatoração

Para cada projeto, após a Fase 3:

```bash
# Python/Flask
pip install -r requirements.txt
python app.py
# Testar endpoints com curl ou httpie

# Node.js/Express
npm install
npm start
# Testar endpoints com curl ou arquivo api.http
```

### Estrutura do Repositório

```
mba-ia-refactor-projects-skill/
├── README.md
├── code-smells-project/
│   ├── .claude/skills/refactor-arch/   # Skill original
│   └── (código fonte)
├── ecommerce-api-legacy/
│   ├── .claude/skills/refactor-arch/   # Cópia da skill
│   └── (código fonte)
├── task-manager-api/
│   ├── .claude/skills/refactor-arch/   # Cópia da skill
│   └── (código fonte)
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```
