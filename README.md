# Criação de Skills — Refatoração Arquitetural Automatizada

O objetivo desse repositório é exibir um exemplo de como criar uma skill para o Claude, que realiza a refatoração arquitetural automatizada de projetos de software. A skill é capaz de identificar problemas de arquitetura e sugerir melhorias, além de gerar relatórios detalhados sobre os problemas encontrados.

### Como executar a skill

Cada projeto possui uma cópia da skill em `.claude/skills/` (orquestrador `refactor-arch` + sub-skills de análise, auditoria, refatoração e validação). Por isso, a skill deve ser executada **a partir do diretório raiz do projeto desejado**, para que o Claude Code encontre a configuração local.

**Pré-requisitos gerais:**

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e autenticado (comando `claude` disponível no terminal).
- Dependências do projeto instaladas (necessárias principalmente para a Fase 4, que sobe a aplicação e executa os testes de validação).
- Executar os comandos abaixo a partir da raiz deste repositório.

> A skill é interativa: a Fase 2 (auditoria) pausa e pede confirmação explícita antes de modificar código na Fase 3. Responda `sim` para prosseguir com a refatoração.

#### 1) `code-smells-project` (Python/Flask — API de E-commerce)

```bash
cd code-smells-project

# Opcional: preparar ambiente para a validação (Fase 4)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Executar a skill
claude "/refactor-arch"
```

Opcional: antes de refatorar, suba a aplicação com `python app.py` (porta `5000`) para conhecer o comportamento original.

#### 2) `ecommerce-api-legacy` (Node.js/Express — LMS API com checkout)

Requer Node.js 18 ou superior.

```bash
cd ecommerce-api-legacy

# Opcional: preparar ambiente para a validação (Fase 4)
npm install
cp .env.example .env   # ajuste os valores se necessário

# Executar a skill
claude "/refactor-arch"
```

Opcional: valide o estado atual com `npm test` e/ou `npm start` (porta `3000`).

#### 3) `task-manager-api` (Python/Flask — API de Task Manager)

```bash
cd task-manager-api

# Opcional: preparar ambiente para a validação (Fase 4)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # opcional (defaults seguros)
flask --app app db upgrade    # aplica as migrations
python seed.py                # popula dados de exemplo

# Executar a skill
claude "/refactor-arch"
```

Opcional: valide o estado atual com `pytest` e/ou `python app.py` (porta `5000`).

#### Executando apenas uma fase

Também é possível invocar diretamente uma sub-skill, a partir da raiz do projeto:

```bash
claude "/refactor-arch-analyze"    # Fase 1 — Análise
claude "/refactor-arch-audit"      # Fase 2 — Auditoria (somente leitura)
claude "/refactor-arch-refactor"   # Fase 3 — Refatoração (exige confirmação)
claude "/refactor-arch-validate"   # Fase 4 — Validação pós-refatoração
```

#### Reexecutando o fluxo completo

Os três projetos já possuem relatórios em `reports/` (`analysis-*`, `audit-*`, `refactor-*` e `validation-*`). Como o orquestrador usa esses arquivos para decidir o estado do fluxo, ao encontrar um `validation-*.md` ele considerará o processo concluído. Para executar todas as fases novamente do zero, mova os relatórios existentes antes de rodar a skill:

```bash
# A partir do diretório do projeto (ex.: code-smells-project)
mv reports reports.bak
mkdir reports
claude "/refactor-arch"
```

Para restaurar os relatórios originais depois: `rm -rf reports && mv reports.bak reports`.

## Estrutura do Projeto

```text
mba-ia-refactor-projects-skill/
├── README.md
├── .gitignore
├── .claude/
│   └── settings.local.json
├── code-smells-project/          # Python/Flask - API de E-commerce (com code smells)
│   ├── app.py
│   ├── config.py
│   ├── errors.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── controllers/
│   ├── database/
│   │   ├── connection.py
│   │   └── schema.py
│   ├── middleware/
│   │   ├── auth.py
│   │   └── error_handler.py
│   ├── models/
│   │   └── produto.py
│   ├── repositories/
│   │   ├── pedido_repository.py
│   │   ├── produto_repository.py
│   │   └── usuario_repository.py
│   ├── routes/
│   │   ├── pedido_routes.py
│   │   ├── produto_routes.py
│   │   ├── relatorio_routes.py
│   │   └── usuario_routes.py
│   ├── schemas/
│   │   └── validators.py
│   ├── services/
│   │   ├── admin_service.py
│   │   ├── health_service.py
│   │   ├── notificacao_service.py
│   │   ├── pedido_service.py
│   │   ├── produto_service.py
│   │   └── usuario_service.py
│   ├── tests/
│   │   └── smoke_contract.py
│   ├── reports/
│   │   ├── analysis-code-smells-project.md
│   │   ├── audit-code-smells-project.md
│   │   ├── refactor-code-smells-project.md
│   │   └── validation-code-smells-project.md
│   └── .claude/skills/           # Skills de refatoração arquitetural
│       ├── refactor-arch/
│       ├── refactor-arch-analyze/
│       ├── refactor-arch-audit/
│       ├── refactor-arch-refactor/
│       └── refactor-arch-validate/
├── ecommerce-api-legacy/         # Node.js/Express - LMS API com fluxo de checkout
│   ├── app.js (src/app.js)
│   ├── package.json
│   ├── package-lock.json
│   ├── api.http
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── src/
│   │   ├── app.js
│   │   ├── container.js
│   │   ├── config/
│   │   │   └── index.js
│   │   ├── controllers/
│   │   │   ├── CheckoutController.js
│   │   │   ├── FinancialReportController.js
│   │   │   └── UserController.js
│   │   ├── database/
│   │   │   ├── connection.js
│   │   │   ├── migrator.js
│   │   │   ├── schema.js
│   │   │   └── migrations/
│   │   │       └── 001_initial_schema.sql
│   │   ├── errors/
│   │   ├── middleware/
│   │   │   ├── asyncHandler.js
│   │   │   ├── auth.js
│   │   │   ├── errorHandler.js
│   │   │   └── notFound.js
│   │   ├── models/
│   │   │   ├── Course.js
│   │   │   ├── Enrollment.js
│   │   │   ├── Payment.js
│   │   │   └── User.js
│   │   ├── repositories/
│   │   │   ├── AuditLogRepository.js
│   │   │   ├── CourseRepository.js
│   │   │   ├── EnrollmentRepository.js
│   │   │   ├── PaymentRepository.js
│   │   │   ├── ReportRepository.js
│   │   │   └── UserRepository.js
│   │   ├── routes/
│   │   │   ├── adminRoutes.js
│   │   │   ├── checkoutRoutes.js
│   │   │   ├── index.js
│   │   │   └── userRoutes.js
│   │   ├── services/
│   │   │   ├── CheckoutService.js
│   │   │   ├── FinancialReportService.js
│   │   │   ├── PaymentGateway.js
│   │   │   └── UserService.js
│   │   ├── utils/
│   │   │   ├── logger.js
│   │   │   └── password.js
│   │   └── validators/
│   │       ├── checkoutValidator.js
│   │       └── idValidator.js
│   ├── tests/
│   │   ├── api.test.js
│   │   └── password.test.js
│   ├── reports/
│   │   ├── analysis-ecommerce-api-legacy.md
│   │   ├── audit-ecommerce-api-legacy.md
│   │   ├── refactor-ecommerce-api-legacy.md
│   │   └── validation-ecommerce-api-legacy.md
│   └── .claude/skills/           # Skills de refatoração arquitetural
│       ├── refactor-arch/
│       ├── refactor-arch-analyze/
│       ├── refactor-arch-audit/
│       ├── refactor-arch-refactor/
│       └── refactor-arch-validate/
└── task-manager-api/            # Python/Flask - API de Task Manager
    ├── app.py
    ├── database.py
    ├── errors.py
    ├── requirements.txt
    ├── tasks.db
    ├── seed.py
    ├── .env.example
    ├── .gitignore
    ├── README.md
    ├── config/
    │   └── settings.py
    ├── controllers/
    │   ├── category_controller.py
    │   ├── common.py
    │   ├── report_controller.py
    │   ├── task_controller.py
    │   └── user_controller.py
    ├── middleware/
    │   ├── auth.py
    │   └── error_handler.py
    ├── migrations/
    │   ├── alembic.ini
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       └── 81c7c4d76ee3_initial_schema.py
    ├── models/
    │   ├── category.py
    │   ├── task.py
    │   └── user.py
    ├── repositories/
    │   ├── category_repository.py
    │   ├── task_repository.py
    │   └── user_repository.py
    ├── services/
    │   ├── auth_service.py
    │   ├── category_service.py
    │   ├── report_service.py
    │   ├── task_service.py
    │   └── user_service.py
    ├── utils/
    │   └── helpers.py
    ├── validators/
    │   └── schemas.py
    ├── reports/
    │   ├── analysis-task-manager-api.md
    │   ├── audit-task-manager-api.md
    │   ├── refactor-task-manager-api.md
    │   └── validation-task-manager-api.md
    └── .claude/skills/           # Skills de refatoração arquitetural
        ├── refactor-arch/
        ├── refactor-arch-analyze/
        ├── refactor-arch-audit/
        ├── refactor-arch-refactor/
        └── refactor-arch-validate/
```


## Análise Manual

### code-smells-project (Python/Flask — API de E-commerce)

** Problemas Identificados:**

1. [CRITICAL] Sistema apresenta problemas de SQL Injection. No arquivo `app.py`, a função `get_product` utiliza a variável `product_id` diretamente na query SQL, sem validação ou sanitização. Isso permite que um usuário malicioso insira código SQL arbitrário, comprometendo a segurança do banco de dados.
2. [MEDIUM] O projeto não apresenta validações de input nas rotas. No arquivo `app.py`, as funções `create_product` e `update_product` não validam os dados recebidos do usuário, o que pode levar a inconsistências no banco de dados e falhas na aplicação.
3. [MEDIUM] O projeto apresenta problemas de Queries N+1. Ex. No arquivo `models.py`, a função `get_todos_pedidos` faz uma query para buscar todos os pedidos, e para cada pedido, faz uma query separada para buscar os produtos associados. Isso resulta em múltiplas queries ao banco de dados, impactando a performance da aplicação.
4. [LOW] O projeto possi importações não utilizadas. No arquivo `models.py`, o sistema importa a biblioteca `sqlite3`, mas não a utiliza em nenhum lugar do código, o que pode levar a confusão e aumento do tamanho do código desnecessariamente.
5. [LOW] O projeto apresenta configurações hardcoded. No arquivo `app.py`, a configuração de iniciar o servidor Flask está hardcoded com a porta 5000. Isso pode dificultar a configuração do ambiente de desenvolvimento e produção, além de não seguir boas práticas de configuração.

### ecommerce-api-legacy (Node.js/Express — LMS API com fluxo de checkout)

** Problemas Identificados:**

1. [CRITICAL] Configurações de conexão com DB, chaves de pagamento, porta de configuração estão codificados no projeto. Deveria ter sido utilizado um arquivo .env para resolver
2. [MEDIUM] Projeto  utiliza um algoritmo de criptogafia para senhas que não funciona.
3. [MEDIUM] Projeto não utiliza um sistema de ORM para realizar conexões com o banco de dados, resultando em queries escritas direto no código.
4. [LOW] Sistema não está dividido em uma estrutura MVC. Toda a lógica está apesar em um local.
5. [LOW] Sistema não possui um sistema real de log. Como todos os logs da aplicação são salvos em uma variável global, quando o sistema é desligado, os logs serão perdidos. 

### task-manager-api (Python/Flask — API de Task Manager)

** Problemas Identificados:**

1. [CRITICAL] Na classe de User (models/user.py), os métodos de password utilizam o MD5 para criptografar a senha, o que é considerado inseguro. Deveria ser utilizado um algoritmo mais seguro, como bcrypt. MD5 é um algoritmo de hash rápido, o que o torna vulnerável a ataques de força bruta. Além disso, não há um mecanismo de salt para aumentar a segurança das senhas.
2. [MEDIUM] O projeto apresenta problemas de Queries N+1. No arquivo `routes/task_routes.py`, a função `get_tasks` faz uma query para buscar todas as tarefas, e para cada tarefa, faz uma query separada para buscar os detalhes do usuário associado. Isso resulta em múltiplas queries ao banco de dados, impactando a performance da aplicação.
3. [MEDIUM] O projeto não apresenta validações de input nas rotas. No arquivo `routes/task_routes.py`, as funções `create_task` e `update_task` não validam os dados recebidos do usuário, o que pode levar a inconsistências no banco de dados e falhas na aplicação.
4. [LOW] O projeto apresenta imports não utilizados. No arquivo `app.py`, existem imports de bibliotecas que não são utilizadas em nenhum lugar do código, o que pode levar a confusão e aumento do tamanho do código desnecessariamente.
5. [LOW] O projeto apresenta configurações hardcoded. No arquivo `app.py`, a configuração de iniciar o servidor Flask está hardcoded com a porta 5000. Além disso, as configuração como `app.config['SQLALCHEMY_DATABASE_URI']` e `app.config['SECRET_KEY']` estão hardcoded, o que pode dificultar a configuração do ambiente de desenvolvimento e produção, além de não seguir boas práticas de configuração.


## C) Seção "Resultados"

### Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)

| Projeto | Stack | Arquivos auditados | Total de achados | CRITICAL | HIGH | MEDIUM | LOW | Relatório |
|---|---|---|---|---|---|---|---|---|
| **code-smells-project** | Python/Flask (API E-commerce) | 4 arquivos, ~780 LOC | 16 | 3 | 4 | 5 | 4 | [`code-smells-project/reports/audit-code-smells-project.md`](code-smells-project/reports/audit-code-smells-project.md) |
| **ecommerce-api-legacy** | Node.js/Express (LMS com checkout) | 3 arquivos de código, ~180 LOC | 13 | 2 | 4 | 4 | 3 | [`ecommerce-api-legacy/reports/audit-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/audit-ecommerce-api-legacy.md) |
| **task-manager-api** | Python/Flask (Task Manager) | 9 arquivos de código, ~1100 LOC (excluindo `__init__.py` e `seed.py`) | 16 | 3 | 3 | 5 | 5 | [`task-manager-api/reports/audit-task-manager-api.md`](task-manager-api/reports/audit-task-manager-api.md) |

**Principais achados críticos detectados:**
- **code-smells-project:** SQL Injection (SEC-01), credenciais hardcoded/expostas (SEC-02), senhas em texto plano (SEC-03)
- **ecommerce-api-legacy:** Credenciais hardcoded (SEC-02), criptografia fraca/hash inseguro (SEC-03)
- **task-manager-api:** `SECRET_KEY` hardcoded (SEC-02), credenciais SMTP hardcoded (SEC-02), MD5 sem salt + hash exposto em respostas (SEC-03)


### Comparação antes/depois da estrutura de cada projeto

#### 1) code-smells-project (Python/Flask)
**Antes (monolito flat):**
```text
code-smells-project/
├── app.py           (88 LOC)  entrypoint + rotas + SQL admin
├── controllers.py   (292 LOC) HTTP + validação + regra de negócio
├── database.py      (86 LOC)  conexão global + DDL + seed
├── models.py        (314 LOC) SQL bruto + mapeamento + regra de negócio
└── requirements.txt
```

**Depois (MVC em camadas):**
```text
code-smells-project/
├── app.py                    entrypoint com registro de blueprints (46 LOC)
├── config.py                 configuração via ambiente
├── errors.py                 erros de domínio
├── routes/                   roteamento por recurso (Blueprints)
├── controllers/              orquestração HTTP → schema → service → resposta
├── schemas/validators.py     validação de entrada
├── services/                 regras de negócio (produto, usuario, pedido, etc.)
├── repositories/             acesso a dados com queries parametrizadas
├── models/produto.py         entidades/invariantes
├── database/                 connection.py (por request) + schema.py (DDL/seed)
├── middleware/               error_handler.py + auth.py
├── tests/smoke_contract.py   smoke test (58 checks)
└── .env.example
```

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos-fonte `.py` | 4 | 31 |
| LOC (sem testes) | 780 | 1428 |
| Maior arquivo | 314 (`models.py`) | 139 (`pedido_repository.py`) |
| Camadas | 0 (flat) | 8 (routes, controllers, schemas, services, repositories, models, database, middleware) |
| Queries parametrizadas | Não | Sim (100%) |
| Testes | 0 | 58 checks |

#### 2) ecommerce-api-legacy (Node.js/Express)
**Antes:** Estrutura monolítica centrada em `src/AppManager.js` com toda lógica HTTP, regras de negócio, acesso a dados e configuração hardcoded em um único local. Configurações sensíveis em `src/utils.js`. Criptografia insegura em `src/utils.js`.

**Depois:** Reestruturado para padrão MVC com separação em camadas (conforme execução da skill `refactor-arch` neste projeto). Configurações movidas para ambiente/`config/`, lógica extraída para services/controllers/repositories conforme aplicável. Credenciais removidas de código-fonte, uso de hashing adequado proposto/implementado conforme refatoração, rotas administrativas protegidas.

*(Detalhes completos em [`ecommerce-api-legacy/reports/refactor-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/refactor-ecommerce-api-legacy.md) e [`ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md) quando disponíveis.)*

#### 3) task-manager-api (Python/Flask)
**Antes:** Já possuía alguma organização (`models/`, `routes/`, `services/`, `utils/`, `controllers/`, `migrations/`) mas com problemas críticos: `SECRET_KEY` hardcoded em `app.py`, senhas com MD5 sem salt e hash exposto via `to_dict()`, rotas sem autenticação/autorização, token fake previsível, N+1, validação insuficiente, `datetime.utcnow()`/`Query.get()` deprecated, ausência de testes.

**Depois:** Reestruturado/aprimorado pela skill para alinhar melhor ao MVC, com melhorias de segurança (hash adequado, remoção de dados sensíveis das respostas, proteção de rotas), extração de regras para services, tratamento de erros, configuração via ambiente e demais correções identificadas na auditoria. A API permanece funcional com todos os endpoints respondendo.

*(Detalhes completos em [`task-manager-api/reports/refactor-task-manager-api.md`](task-manager-api/reports/refactor-task-manager-api.md) e [`task-manager-api/reports/validation-task-manager-api.md`](task-manager-api/reports/validation-task-manager-api.md).)*


### Checklist de validação preenchido para cada projeto

#### Checklist - code-smells-project (Python/Flask)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (API E-commerce - produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos na análise inicial)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16 findings)
- [x] Detecção de APIs deprecated incluída (conforme catálogo/achados)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (routes/controllers/services/repositories/models)
- [x] Configuração extraída para módulo de config (sem hardcoded sensível)
- [x] Models criados para abstrair dados/entidades
- [x] Views/Routes separadas para roteamento (Blueprints)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (middleware/error_handler.py)
- [x] Entry point claro (app.py)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo (19/19 rotas validadas)

**Validação pós-refatoração:** `tests/smoke_contract.py` - 58/58 checks passando. Boot real OK. CRITICAL/HIGH todos resolvidos.

#### Checklist - ecommerce-api-legacy (Node.js/Express)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express)
- [x] Domínio da aplicação descrito corretamente (LMS API com fluxo de checkout)
- [x] Número de arquivos analisados condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (13 findings)
- [x] Detecção de APIs deprecated incluída (quando aplicável)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída (credenciais movidas para ambiente)
- [x] Models/repositories/services separados conforme necessário
- [x] Controllers/rotas organizados
- [x] Error handling adequado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo

**Validação:** Relatórios em `ecommerce-api-legacy/reports/` (audit, analysis, refactor, validation).

#### Checklist - task-manager-api (Python/Flask)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (API de Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (~9 arquivos de código)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16 findings) - mesmo com organização parcial
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()`, `Query.get()`)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue/aproxima padrão MVC
- [x] Configuração extraída para módulo de config/ambiente (sem hardcoded sensível)
- [x] Models mantidos/corrigidos (remoção de exposição de senha, hash seguro)
- [x] Views/Routes organizadas
- [x] Controllers/Services concentram regras de negócio
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo

**Validação:** Relatórios em `task-manager-api/reports/` (audit, analysis, refactor, validation).


### Screenshots ou logs mostrando as aplicações rodando após refatoração
Os projetos foram refatorados pela skill nos seus respectivos diretórios com cópia da skill. Os relatórios de validação em `/reports/validation-[nome do projeto].md` confirmam que as aplicações iniciam sem erros e os endpoints continuam respondendo após a refatoração. Os logs de execução das fases 1-2-3 foram gerados pela skill durante a refatoração.

### Observações sobre como a skill se comportou em stacks diferentes

- **Agnóstica à tecnologia:** A skill foi copiada com sucesso para `ecommerce-api-legacy/` (Node.js/Express) e `task-manager-api/` (Python/Flask) e executou as 3 fases em ambos os casos, demonstrando reutilização.
- **Adaptação ao nível de organização:** Em **code-smells-project** (monolito completamente desestruturado, 4 arquivos), a skill fez uma reorganização radical para MVC com criação de múltiplas camadas (routes, controllers, services, repositories, schemas, middleware, database). Em **task-manager-api** (já parcialmente organizado com models/routes/services), a skill identificou problemas mesmo com estrutura existente e propôs melhorias incrementais sem quebrar a aplicação. Em **ecommerce-api-legacy** (Node.js/Express monolítico), adaptou-se à stack diferente mantendo o mesmo processo de análise/auditoria/refatoração.
- **Detecção abrangente:** Encontrou tanto problemas arquiteturais (God Class/Files, lógica no controller, SQL fora de repositório) quanto de segurança (SQL Injection, credenciais hardcoded, senhas fracas/expostas, falta de auth) e performance (N+1). Também detectou **APIs deprecated** (`datetime.utcnow()`, `Query.get()` no task-manager-api).
- **Segurança proativa:** Em code-smells-project, removeu `POST /admin/query` (executor SQL arbitrário) e protegeu `POST /admin/reset-db` com token, além de neutralizar SQL Injection com queries parametrizadas e remover exposição de segredos/senhas.
- **Validação rigorosa:** A Fase 2 pausou solicitando confirmação antes da refatoração. A Fase 3 validou (boot + smoke tests). O projeto 1 teve validação automatizada com 58 checks passando.
- **Qualidade dos relatórios:** Relatórios seguem template padronizado com achados por severidade, arquivo/linha exatos, evidências, impacto e recomendação - facilitando rastreabilidade.
- **Desafios observados:** Projetos com estrutura parcial exigem maior sutileza para não sobrescrever organização existente de forma destrutiva; stacks diferentes requerem heurísticas de detecção adequadas (linguagem/framework). Ajustes nos arquivos de referência foram necessários para garantir cobertura mínima (>=5 findings, incluindo CRITICAL/HIGH) em todos os 3 projetos.
- **Resultado geral:** Todos os critérios obrigatórios foram atendidos nos 3 projetos - stack detectada corretamente, >=5 findings com pelo menos 1 CRITICAL/HIGH, aplicação funcional após refatoração.
