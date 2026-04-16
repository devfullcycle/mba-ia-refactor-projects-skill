# Skill refactor-arch — Refatoracao Arquitetural Automatizada

Skill para Claude Code que analisa, audita e refatora projetos backend para o padrao MVC, de forma agnostica de tecnologia.

## Analise Manual

### Projeto 1: code-smells-project (Python/Flask — E-commerce API)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **SQL Injection em todas as queries** | CRITICAL | models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 188-224, 280-297 | Todas as queries SQL usam concatenacao de strings (`"SELECT * FROM x WHERE id = " + str(id)`). O login (models.py:109-111) permite bypass de autenticacao. |
| 2 | **Credenciais hardcoded e dados sensiveis expostos** | CRITICAL | app.py:7-8, database.py:76-84, controllers.py:287-289 | SECRET_KEY `'minha-chave-super-secreta-123'` no codigo. Health endpoint expoe secret_key, debug mode e db_path. Senhas fracas no seed. |
| 3 | **Senhas armazenadas em texto plano** | CRITICAL | models.py:105-120 | Senhas sem hash no banco. Comparacao direta de strings para autenticacao. |
| 4 | **Endpoint de execucao arbitraria de SQL** | CRITICAL | app.py:59-78 | `/admin/query` aceita e executa qualquer SQL sem autenticacao. DROP TABLE, SELECT de dados sensiveis — tudo possivel. |
| 5 | **God File — models.py com 314 linhas e 4 dominios** | HIGH | models.py:1-314 | Um unico arquivo contem toda logica de dados para produtos, usuarios, pedidos e relatorios. Impossivel testar em isolamento. |
| 6 | **N+1 Query Problem** | MEDIUM | models.py:187-200, 219-231 | Loops aninhados com cursor2/cursor3 para buscar itens e nomes de produto por pedido. |
| 7 | **Duplicacao de validacao** | MEDIUM | controllers.py:30-35, 74-79 | Mesma validacao de produto copiada entre criar e atualizar. |
| 8 | **Print-based logging** | LOW | controllers.py:8, 57, 106, 161, 208 | `print()` ao inves de `logging` framework. |
| 9 | **Sem constraints no banco** | LOW | database.py:8-40 | Sem FOREIGN KEY, UNIQUE, NOT NULL ou CHECK constraints. |

### Projeto 2: ecommerce-api-legacy (Node.js/Express — LMS API)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **Credenciais e API keys hardcoded** | CRITICAL | src/utils.js:1-7 | Credenciais de DB, gateway de pagamento, SMTP todas expostas em texto plano no codigo. |
| 2 | **Password "hashing" com Base64** | CRITICAL | src/utils.js:17-23 | Funcao `badCrypto()` usa Base64 encoding (reversivel) como "criptografia". Nao oferece protecao real. |
| 3 | **Secrets logados no console** | CRITICAL | src/AppManager.js:45 | Chave do gateway de pagamento e numero de cartao parcialmente logados com `console.log()`. |
| 4 | **Callback Hell (6-7 niveis)** | HIGH | src/AppManager.js:28-78, 80-129 | Callbacks profundamente aninhados no checkout e relatorio financeiro. Tratamento de erros inconsistente. |
| 5 | **Sem autenticacao em endpoints admin** | HIGH | src/AppManager.js:80, 131 | Relatorio financeiro e delete de usuarios acessiveis publicamente. |
| 6 | **N+1 queries no relatorio** | MEDIUM | src/AppManager.js:80-129 | Queries aninhadas por curso, matricula, usuario e pagamento. |
| 7 | **Estado global mutavel** | MEDIUM | src/utils.js:9-10 | `globalCache = {}` sem TTL ou limites. `totalRevenue` exportado mas nunca usado. |
| 8 | **Validacao de pagamento trivial** | MEDIUM | src/AppManager.js:45-46 | Cartao aceito se comeca com "4". Sem integracao real. |
| 9 | **Nomes de variaveis ilegveis** | LOW | src/AppManager.js:29-33 | Variaveis `u`, `e`, `p`, `cid`, `cc` ao inves de nomes descritivos. |

### Projeto 3: task-manager-api (Python/Flask — Task Manager)

| # | Problema | Severidade | Arquivo:Linha | Justificativa |
|---|----------|------------|---------------|---------------|
| 1 | **Password hashing com MD5** | CRITICAL | models/user.py:29, 32 | MD5 criptograficamente quebrado desde 2004. Senhas reversiveis com rainbow tables em minutos. |
| 2 | **Credenciais hardcoded** | CRITICAL | app.py:13, services/notification_service.py:9-10 | SECRET_KEY e credenciais de email no codigo. `python-dotenv` nas deps mas nao usado para secrets. |
| 3 | **JWT fake sem autenticacao real** | CRITICAL | routes/user_routes.py:210 | Token `'fake-jwt-token-' + str(user.id)`. Nenhum endpoint valida tokens. API inteira e publica. |
| 4 | **Hash de senha exposto na API** | HIGH | models/user.py:21, routes/user_routes.py:20-21 | `to_dict()` retorna campo `password`. Combinado com MD5, senhas sao reversiveis por qualquer cliente. |
| 5 | **Duplicacao massiva de codigo** | HIGH | routes/task_routes.py:17-28, 30-39 (5 locais) | Logica overdue duplicada em 5 locais. Conversao task-to-dict duplicada. Validacao triplicada. |
| 6 | **Bare except clauses** | MEDIUM | routes/task_routes.py:62, 137, 151, 221, 236; routes/user_routes.py:130, 149 | 11+ locais com `except:` generico mascarando erros reais. |
| 7 | **N+1 queries** | MEDIUM | routes/task_routes.py:41-48, 50-57 | Query separada por task para buscar usuario e categoria. |
| 8 | **Loops Python para agregacao** | MEDIUM | routes/report_routes.py:30-43, 53-68, 119-135 | Carrega tudo na memoria para contar. Deveria usar SQL GROUP BY. |
| 9 | **datetime.utcnow() deprecated** | LOW | models/user.py:14, models/task.py:16-17, models/category.py:12 | Deprecated desde Python 3.12. Substituir por `datetime.now(timezone.utc)`. |

---

## Construcao da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                       # Prompt principal — define as 3 fases
├── project-analysis.md            # Heuristicas de deteccao de stack
├── anti-patterns-catalog.md       # Catalogo de 16 anti-patterns com severidades
├── audit-report-template.md       # Template padronizado do relatorio
├── mvc-architecture-guidelines.md # Regras do padrao MVC alvo
└── refactoring-playbook.md        # 10 padroes de transformacao com antes/depois
```

### Decisoes de Design

**SKILL.md como orquestrador:** O SKILL.md funciona como um prompt que instrui o agente sobre o fluxo das 3 fases sequenciais. Ele referencia os arquivos de conhecimento sem duplicar conteudo, mantendo cada responsabilidade isolada.

**Catalogo de anti-patterns extenso:** Inclui 16 anti-patterns cobrindo todas as severidades:
- CRITICAL (3): SQL Injection, Hardcoded Credentials, Insecure Password Storage
- HIGH (3): God Class, Missing Authentication, Callback Hell
- MEDIUM (6): N+1 Queries, Code Duplication, Missing Validation, Sensitive Data Exposure, Global Mutable State, Poor Error Handling
- LOW (3): Missing DB Constraints, Magic Numbers, No Pagination
- Bonus: Secao dedicada a APIs deprecated (Python e Node.js)

**Playbook com 10 padroes de transformacao:** Cada padrao tem exemplos concretos antes/depois em Python E Node.js, garantindo que a skill funcione em ambas as stacks. Padroes cobrem desde extrair configuracao ate centralizar error handling.

**Agnosticismo de tecnologia:** Todos os arquivos de referencia fornecem exemplos em Python e Node.js. As heuristicas de deteccao cobrem ambos os ecossistemas. O template de relatorio e generico.

### Desafios e Solucoes

1. **Deteccao de stack:** Criado arquivo `project-analysis.md` com tabelas de mapeamento arquivo/import -> tecnologia, cobrindo Python, Node.js e outros.
2. **Consistencia do relatorio:** Template rigido em `audit-report-template.md` com regras de ordenacao, minimos obrigatorios e formato de referencia a arquivos.
3. **Pausa obrigatoria:** SKILL.md explicita que a Fase 2 DEVE pedir confirmacao antes de qualquer modificacao, com prompt padronizado.
4. **Adaptacao a projetos parcialmente organizados:** O playbook inclui orientacoes para projetos que ja possuem alguma estrutura, focando em melhorias incrementais sem quebrar o que funciona.

---

## Resultados

### Resumo dos Relatorios de Auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|----------|------|--------|-----|-------|
| code-smells-project | 4 | 3 | 4 | 3 | 14 |
| ecommerce-api-legacy | 3 | 3 | 4 | 2 | 12 |
| task-manager-api | 3 | 2 | 5 | 3 | 13 |

### Comparacao Antes/Depois

#### Projeto 1: code-smells-project

**Antes:**
```
code-smells-project/
├── app.py          (88 linhas — config + rotas admin + server)
├── controllers.py  (292 linhas — toda logica de request handling)
├── models.py       (314 linhas — toda logica de dados, 4 dominios)
└── database.py     (86 linhas — conexao + schema + seed)
```

**Depois (estrutura MVC alvo):**
```
code-smells-project/
├── config/
│   └── settings.py          # Configuracao via env vars
├── models/
│   ├── database.py           # Conexao e inicializacao
│   ├── product_model.py      # CRUD produtos (queries parametrizadas)
│   ├── user_model.py         # CRUD usuarios (bcrypt hashing)
│   └── order_model.py        # CRUD pedidos (com JOINs)
├── controllers/
│   ├── product_controller.py # Logica de negocio produtos
│   ├── user_controller.py    # Logica de negocio usuarios
│   └── order_controller.py   # Logica de negocio pedidos
├── views/
│   ├── product_routes.py     # Rotas /produtos
│   ├── user_routes.py        # Rotas /usuarios, /login
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
├── app.js           (14 linhas — setup basico)
├── AppManager.js    (141 linhas — TUDO: DB, rotas, logica)
└── utils.js         (25 linhas — config, cache, crypto)
```

**Depois (estrutura MVC alvo):**
```
ecommerce-api-legacy/src/
├── config/
│   └── settings.js           # Env vars (dotenv)
├── models/
│   ├── database.js            # Conexao SQLite promisificada
│   ├── userModel.js           # CRUD usuarios (bcrypt)
│   ├── courseModel.js          # CRUD cursos
│   └── enrollmentModel.js     # Matriculas + pagamentos
├── controllers/
│   ├── checkoutController.js  # Logica de checkout
│   └── reportController.js    # Logica de relatorios
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
│   ├── task.py                # Task model (metodos utilitarios)
│   └── category.py            # Category model
├── controllers/
│   ├── task_controller.py     # Logica de tarefas
│   ├── user_controller.py     # Logica de usuarios
│   └── report_controller.py   # Logica de relatorios
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

### Checklist de Validacao

#### Projeto 1 — code-smells-project

**Fase 1 — Analise:**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Dominio da aplicacao descrito corretamente (E-commerce API)
- [x] Numero de arquivos analisados condiz com a realidade (4)

**Fase 2 — Auditoria:**
- [x] Relatorio segue o template definido nos arquivos de referencia
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL -> LOW)
- [x] Minimo de 5 findings identificados (14 encontrados)
- [x] Deteccao de APIs deprecated incluida
- [x] Skill pausa e pede confirmacao antes da Fase 3

**Fase 3 — Refatoracao:**
- [x] Estrutura de diretorios segue padrao MVC
- [x] Configuracao extraida para modulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicacao
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicacao inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Analise:**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Dominio da aplicacao descrito corretamente (LMS API com checkout)
- [x] Numero de arquivos analisados condiz com a realidade (3)

**Fase 2 — Auditoria:**
- [x] Relatorio segue o template definido nos arquivos de referencia
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL -> LOW)
- [x] Minimo de 5 findings identificados (12 encontrados)
- [x] Deteccao de APIs deprecated incluida
- [x] Skill pausa e pede confirmacao antes da Fase 3

**Fase 3 — Refatoracao:**
- [x] Estrutura de diretorios segue padrao MVC
- [x] Configuracao extraida para modulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicacao
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicacao inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 3 — task-manager-api

**Fase 1 — Analise:**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0)
- [x] Dominio da aplicacao descrito corretamente (Task Manager API)
- [x] Numero de arquivos analisados condiz com a realidade (12)

**Fase 2 — Auditoria:**
- [x] Relatorio segue o template definido nos arquivos de referencia
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL -> LOW)
- [x] Minimo de 5 findings identificados (13 encontrados)
- [x] Deteccao de APIs deprecated incluida (datetime.utcnow)
- [x] Skill pausa e pede confirmacao antes da Fase 3

**Fase 3 — Refatoracao:**
- [x] Estrutura de diretorios segue padrao MVC
- [x] Configuracao extraida para modulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicacao
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicacao inicia sem erros
- [x] Endpoints originais respondem corretamente

### Observacoes sobre Comportamento em Stacks Diferentes

- **Python/Flask (Projetos 1 e 3):** A skill detecta corretamente Flask via imports e `requirements.txt`. Os padroes de transformacao (queries parametrizadas, werkzeug password hashing, Flask blueprints) funcionam diretamente.
- **Node.js/Express (Projeto 2):** A skill detecta Express via `package.json`. A principal diferenca e a transformacao de callbacks para async/await e o uso de `bcrypt` para Node.js ao inves de `werkzeug`.
- **Projeto parcialmente organizado (Projeto 3):** A skill identifica a estrutura existente e propoe melhorias incrementais — por exemplo, extrair controllers das rotas que ja existem e substituir MD5 por bcrypt, sem destruir a organizacao que ja funciona.

---

## Como Executar

### Pre-requisitos

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

### Validar a Refatoracao

Para cada projeto, apos a Fase 3:

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

### Estrutura do Repositorio

```
mba-ia-refactor-projects-skill/
├── README.md
├── code-smells-project/
│   ├── .claude/skills/refactor-arch/   # Skill original
│   └── (codigo fonte)
├── ecommerce-api-legacy/
│   ├── .claude/skills/refactor-arch/   # Copia da skill
│   └── (codigo fonte)
├── task-manager-api/
│   ├── .claude/skills/refactor-arch/   # Copia da skill
│   └── (codigo fonte)
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```
