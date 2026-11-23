# Relatório de Criação e Execução da Skill `refactor-arch`

Neste documento descrevo as etapas, decisões arquiteturais e resultados obtidos na concepção e aplicação da skill **`refactor-arch`**, desenvolvida para auditar, documentar e refatorar aplicações legadas para o padrão MVC de forma automatizada e agnóstica de tecnologia.

---

## A) Análise Manual dos Projetos

Antes de automatizar o processo via IA, realizei a inspeção manual dos 3 projetos fornecidos. **Recomendei expressamente a verificação e classificação prévia de cada problema por níveis de severidade**, evitando refatorações cegas e estabelecendo critérios objetivos de priorização:

- **CRITICAL**: Falhas de segurança exploráveis e violação total de responsabilidade arquitetural.
- **HIGH**: Quebra severa do padrão MVC/SOLID, acoplamento indevido ou estado global mutável.
- **MEDIUM**: Gargalos de performance (como queries N+1), validações ausentes e tratamento genérico de erros.
- **LOW**: Falta de clareza nos contratos HTTP, código morto e números mágicos.

### 1. `code-smells-project` (Python / Flask)
- **[CRITICAL] SQL Injection & Execução Arbitrária (`app.py:59-78` / `models.py`)**: O endpoint `/admin/query` recebia SQL puro no payload JSON e executava diretamente no SQLite sem sanitização. Além disso, queries eram construídas por concatenação de strings.
  - *Relevância*: Risco catastrófico de perda total de dados, exfiltração e bypass de autenticação.
- **[CRITICAL] Credenciais Hardcoded & Endpoint Administrativo Aberto (`app.py:7-8, 47-57`)**: `SECRET_KEY` fixa no código e exposta na rota pública `/health`, junto ao endpoint `/admin/reset-db` desprotegido.
  - *Relevância*: Comprometimento da integridade de sessões e possibilidade de reset malicioso do banco em produção.
- **[CRITICAL] Monólito / God Module (`models.py:1-314` e `controllers.py:1-292`)**: Mais de 300 linhas misturando DDL, queries raw SQL, regras de negócio de 4 domínios (produtos, usuários, pedidos, relatórios) e rotas em arquivos únicos.
  - *Relevância*: Violação frontal do SRP; impossibilita testes de unidade e manutenção isolada.
- **[HIGH] Operações de Banco Diretas nos Controllers (`controllers.py:266-275`)**: Consultas SQL (`SELECT 1`, contagens) executadas diretamente dentro das funções de controle HTTP.
  - *Relevância*: Quebra da barreira entre camadas de transporte e persistência.
- **[HIGH] Senhas em Texto Puro (`models.py:72-103`)**: Senhas armazenadas sem hash e retornadas abertamente nos endpoints de listagem de usuários.
  - *Relevância*: Exposição severa de dados confidenciais dos usuários (violação da LGPD/GDPR).
- **[HIGH] Estado Global Mutável (`database.py:4-10`)**: Conexão SQLite mantida em variável global com `check_same_thread=False`.
  - *Relevância*: Risco iminente de race conditions e corrupção de banco em ambientes concorrentes.
- **[MEDIUM] Problema de N+1 Queries (`models.py:171-233`)**: Consultas aninhadas em loops para buscar itens e produtos de cada pedido.
  - *Relevância*: Explosão de I/O de banco e degradação exponencial de latência.
- **[MEDIUM] Heavy Health Check com Contagens Desnecessárias (`controllers.py:266-275` / `health_controller.py`)**: O endpoint `/health` executava contagens totais (`SELECT COUNT(*)`) sobre produtos, usuários e pedidos a cada invocação de probe.
  - *Relevância*: Sondas de infraestrutura (Kubernetes, AWS ALB, monitoramento) disparam periodicamente em intervalos curtos; consultas agregadas desnecessárias causam overhead de I/O e risco de cascading failure sob estresse, quando o correto é validar apenas a conectividade atômica (`SELECT 1`).
- **[LOW] Métodos HTTP Implícitos e Imports Não Utilizados (`app.py:32`, `database.py:2`)**: Rotas sem declaração de método (`methods=['GET']`) e código morto poluindo o namespace.

### 2. `ecommerce-api-legacy` (Node.js / Express)
- **[CRITICAL] Credenciais Hardcoded e Log de Cartão de Crédito (`src/utils.js:1-7`, `src/AppManager.js:45`)**: Chave ativa de gateway de pagamento e senha de banco expostas no código, com log em texto claro do número completo de cartão de crédito no console.
  - *Relevância*: Violação gravíssima de PCI-DSS e vazamento direto de dados financeiros sensíveis.
- **[CRITICAL] God Class Monolítica (`src/AppManager.js:4-139`)**: Classe única concentrando DDL do SQLite, seeds, rotas Express, regras de checkout, relatórios e lógica de persistência.
  - *Relevância*: Acoplamento extremo que inviabiliza testes, modularização e evolução do sistema.
- **[HIGH] Criptografia Fraca / Caseira (`src/utils.js:17-23`)**: Função `badCrypto()` baseada em loop de Base64 truncado em 10 caracteres e senhas padrão (`'123'`).
  - *Relevância*: Hashes triviais e facilmente quebravéis por ataques de dicionário e colisão.
- **[HIGH] Estado Global Mutável (`src/utils.js:9-15`)**: Objeto `globalCache` e variável `totalRevenue` acumulados no escopo do módulo.
  - *Relevância*: Vazamento de memória e inconsistência em concorrência.
- **[MEDIUM] Callback Hell e N+1 Queries (`src/AppManager.js:80-128`)**: Relatório financeiro disparando queries sequenciais aninhadas controladas por contadores manuais.
  - *Relevância*: Risco de requisições travadas, código ilegível e sobrecarga desnecessária do banco.
- **[MEDIUM] Inconsistência banco  (`src/AppManager.js:131-138`)**: Deletar usuario e deixar registros orfãos nas tabelas correlacionadas.
 -  *Relevância*: Risco de ter banco de dados inconsistente.
- **[LOW] Respostas de Erro em Texto Puro (`src/AppManager.js:35-71`)**: Erros retornados como strings avulsas (`"Erro DB"`) sem padronização JSON.

### 3. `task-manager-api` (Python / Flask + SQLAlchemy)
- **[CRITICAL] Credenciais e Segredos Hardcoded (`app.py:11-13`, `services/notification_service.py:7-10`)**: `SECRET_KEY` e credenciais SMTP com senha em texto puro no código, sem uso do `.env`.
  - *Relevância*: Exposição de credenciais de infraestrutura e serviço de e-mail.
- **[HIGH] Ausência de Camada Controller (`routes/task_routes.py:11-298`)**: As rotas executavam consultas ORM (`Task.query`), manipulação de transações (`db.session.commit()`) e regras de negócio diretamente nos manipuladores HTTP.
  - *Relevância*: Forte acoplamento entre HTTP e regras de negócio, impossibilitando reuso e testes isolados.
- **[HIGH] Hash MD5 Obsoleto e Senha Exposta no DTO (`models/user.py:17-32`)**: Uso de `hashlib.md5()` sem salt e serialização da senha no método `to_dict()`.
  - *Relevância*: Vulnerabilidade contra rainbow tables e vazamento de credenciais na API REST.
- **[MEDIUM] N+1 Queries em Listagens (`routes/task_routes.py:41-58`)**: Queries individuais executadas para cada usuário e categoria dentro da iteração de tarefas.
  - *Relevância*: Latência desnecessária que escala linearmente com o número de registros.
- **[MEDIUM] Deleção Destrutiva de Tarefas em Categorias e Falta de Desvinculação Prévia (`routes/report_routes.py:212-225` / `models/category.py:13`)**: A exclusão de uma categoria apagava em cascata todas as tarefas vinculadas via `cascade='all, delete-orphan'` em vez de desvinculá-las previamente, mesmo sendo a categoria um atributo puramente opcional (`category_id` anulável).
  - *Relevância*: Perda destrutiva e imprevista de tarefas dos usuários durante a exclusão de categorias secundárias de organização.
- **[LOW] API Deprecated `datetime.utcnow()` (`models/user.py:14`)**: Uso de método marcado como obsoleto a partir do Python 3.12 gerando datas sem fuso horário (naive).
  - *Relevância*: Deprecation warnings contínuos e inconsistências temporais.

---

## B) Construção da Skill (`refactor-arch`)

### Decisões de Design
Estruturei a skill em torno de **3 fases estritas e sequenciais** no [SKILL.md](mba-ia-refactor-projects-skill/code-smells-project/.agents/skills/refactor-arch/SKILL.md), apoiadas por uma base modular de conhecimento em `references/`:
1. `references/project_analysis.md`: Heurísticas de detecção de linguagem, framework, banco e diagnóstico arquitetural.
2. `references/antipatterns_catalog.md`: Catálogo padronizado de anti-patterns com severidades e sinais de detecção.
3. `references/report_template.md`: Template consistente para o relatório de auditoria da Fase 2.
4. `references/mvc_guidelines.md`: Regras estruturais e papéis das camadas Model, View/Routes e Controller.
5. `references/refactoring_playbook.md`: Padrões concretos de transformação com exemplos antes/depois.

### Catálogo de Anti-Patterns
Incluí 10 anti-patterns fundamentais cobrindo o ciclo de vida e a saúde de código legado:
- **Segurança**: Injeção de SQL (`SEC-001`), Credenciais Hardcoded (`SEC-002`), Criptografia Quebrada/Insegura (`SEC-003`).
- **Arquitetura**: God Class/God File (`ARCH-001`), Operações de Banco em Controllers/Rotas (`ARCH-002`), Estado Global Mutável (`ARCH-003`), Falta de Rotas Explícitas (`ARCH-004`).
- **Performance & Dados**: N+1 Query Problem (`PERF-001`), Heavy Health Check (`PERF-002`), Deleção Insegura sem Integridade Referencial (`DATA-001`), Deleção Destrutiva em Relacionamentos Opcionais sem Desvinculação Prévia (`DATA-002`).
- **Qualidade & Manutenção**: Tratamento Inconsistente de Erros (`CODE-002`), Alta Complexidade Ciclomática (`CODE-001`), APIs Deprecated (`CODE-005`).

*Justificativa*: Esses padrões mapeiam diretamente as maiores fontes de vulnerabilidades, débitos técnicos e gargalos de performance comuns em sistemas legados.

### Garantia de Abordagem Agnóstica
Para assegurar independência de tecnologia:
- A skill analisa manifestos e arquivos (`requirements.txt`, `package.json`, etc.) dinamicamente para identificar o ecossistema.
- Os princípios arquiteturais focam em **responsabilidades lógicas** (ex: separar orquestração HTTP de regras de negócio e de persistência), independentemente de ser Python (Flask/Blueprints), Node.js (Express/Routers) ou outra linguagem.
- O playbook contém equivalências semânticas conceituais e exemplos práticos para ambas as plataformas.

### Desafios e Soluções
- **Prevenção de alterações precipitadas**: A IA tendia a refatorar arquivos antes de auditar completamente. Resolvi instituindo um **portão de parada obrigatório (human-in-the-loop)** no final da Fase 2, exigindo confirmação explícita (`[y/n]`) após a geração do relatório.
- **Projetos com maturidades diferentes**: O Projeto 1 não tinha pastas, enquanto o Projeto 3 já possuía uma divisão preliminar. Modelei a Fase 1 para diagnosticar o estado da arquitetura atual antes de sugerir a nova árvore de diretórios, preservando e evoluindo a estrutura existente sem criar conflitos.

---

## C) Resultados

### Resumo dos Relatórios de Auditoria
A execução da skill auditou com precisão os 3 projetos, identificando e sanando os problemas:

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total Inicial | Total Pós-Refactor |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **code-smells-project** | Python / Flask | 3 | 4 | 4 | 3 | **14** | **0** |
| **ecommerce-api-legacy** | Node.js / Express | 2 | 4 | 2 | 2 | **10** | **0** |
| **task-manager-api** | Python / Flask + SQLAlchemy | 1 | 3 | 4 | 3 | **11** | **0** |

Os relatórios detalhados encontram-se salvos em:
- [reports/audit-project-1.md](mba-ia-refactor-projects-skill/reports/audit-project-1.md)
- [reports/audit-project-2.md](mba-ia-refactor-projects-skill/reports/audit-project-2.md)
- [reports/audit-project-3.md](mba-ia-refactor-projects-skill/reports/audit-project-3.md)

### Comparação Antes / Depois da Estrutura

- **`code-smells-project`**:
  - *Antes*: 4 arquivos na raiz (`app.py`, `controllers.py`, `models.py`, `database.py`) com código monolítico misturado.
  - *Depois*: Estrutura MVC desacoplada em `config/settings.py`, `models/` (modelos por domínio com queries parametrizadas), `controllers/` (regras e orquestração), `views/` (Blueprints de rotas) e `middlewares/error_handler.py`.
- **`ecommerce-api-legacy`**:
  - *Antes*: Monólito `AppManager.js` contendo banco, DDL, rotas e regras de negócio.
  - *Depois*: Módulos limpos em `src/config/`, `src/models/` (classes com queries isoladas), `src/controllers/`, `src/routes/` e `src/middlewares/`. Senhas migradas para hashing seguro e credenciais extraídas para ambiente.
- **`task-manager-api`**:
  - *Antes*: Rotas acessando diretamente o ORM e executando transações e formatações no arquivo de rotas.
  - *Depois*: Introdução formal da camada `controllers/`, isolamento de configurações em `config/settings.py`, remoção de campos sensíveis de serializações e substituição de `datetime.utcnow()` pela moderna `timezone.utc`.

### Checklist de Validação Preenchido

#### Fase 1 — Análise
- [x] Linguagem detectada corretamente nos 3 projetos
- [x] Framework detectado corretamente (Flask e Express)
- [x] Domínio da aplicação descrito corretamente (E-commerce, LMS/Checkout, Task Manager)
- [x] Contagem de arquivos analisados condizente com o projeto

#### Fase 2 — Auditoria
- [x] Relatório seguiu o template padronizado em Markdown
- [x] Cada finding possui arquivo e intervalo exato de linhas
- [x] Findings ordenados estritamente por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados por projeto (obtidos 14, 10 e 11)
- [x] Detecção de APIs obsoletas/deprecated incluída (`datetime.utcnow`)
- [x] Pausa mandatória e solicitação de confirmação humana executada

#### Fase 3 — Refatoração
- [x] Estrutura de diretórios migrada para o padrão MVC limpo
- [x] Configurações extraídas para módulos desacoplados (sem credenciais hardcoded)
- [x] Camada Models criada e operando com queries seguras / ORM
- [x] Views/Routes dedicadas apenas ao roteamento HTTP
- [x] Controllers implementados para orquestrar fluxo e regras de negócio
- [x] Error handling global e centralizado
- [x] Aplicações iniciam sem erros e endpoints originais respondem com sucesso

### Evidências de Execução Pós-Refatoração
Após a refatoração, as aplicações foram executadas e validadas:
- **`code-smells-project`**: Inicialização limpa via Flask na porta 5000; endpoints `/produtos`, `/usuarios`, `/pedidos` e `/health` respondendo 200 OK com payload sanitizado e verificação atômica de conectividade com o banco (`SELECT 1`), eliminando contagens pesadas desnecessárias nas tabelas; endpoint `/admin/query` desativado com segurança.
- **`ecommerce-api-legacy`**: Inicialização via Node.js na porta 3000; rotas de checkout, listagem de cursos e relatório financeiro funcionando sem vazamento de cartão ou credenciais.
- **`task-manager-api`**: Inicialização via Flask; rotas `/tasks`, `/users` e `/reports` operando através dos novos controllers com integridade referencial preservada, desvinculação segura de tarefas ao remover categorias (`SET NULL`) e zero regressão.

### Comportamento em Stacks Diferentes
A skill demonstrou adaptabilidade robusta: reconheceu naturalmente as convenções idiomáticas do Python (Blueprints, SQLAlchemy, decoradores) e do ecossistema Node.js (CommonJS/ES Modules, Express Routers, middlewares de erro `(err, req, res, next)`), aplicando as mesmas diretrizes arquiteturais sem contaminação sintática.

---

## D) Como Executar

### Pré-requisitos
1. CLI configurada no ambiente com suporte a Custom Skills (ex: Gemini CLI, Claude Code ou equivalente).
2. Python 3.10+ com `pip` instalado.
3. Node.js 18+ com `npm` instalado.
4. Repositório clonado localmente com a skill presente em `.agents/skills/refactor-arch` (ou `.claude/skills/refactor-arch` dependendo da CLI adotada).

### Comandos de Execução da Skill

Para rodar o processo automatizado em cada um dos projetos:

```bash
# 1. Projeto Python/Flask (E-commerce)
cd code-smells-project
agy "/refactor-arch" # ou claude "/refactor-arch"

# 2. Projeto Node.js/Express (LMS/Checkout)
cd ../ecommerce-api-legacy
agy "/refactor-arch" # ou claude "/refactor-arch"

# 3. Projeto Python/Flask (Task Manager)
cd ../task-manager-api
agy "/refactor-arch" # ou claude "/refactor-arch"
```

> **Atenção:** Ao final da Fase 2, a skill imprimirá o relatório de auditoria e pausará a execução. Digite `y` para autorizar a Fase 3 (Refatoração).

### Como Validar a Refatoração

Para certificar que as aplicações continuam íntegras e funcionais após a reestruturação:

1. **Testar `code-smells-project` (Python)**:
   ```bash
   cd code-smells-project
   python app.py
   # Em outro terminal:
   curl -i http://localhost:5000/health
   curl -i http://localhost:5000/produtos
   ```

2. **Testar `ecommerce-api-legacy` (Node.js)**:
   ```bash
   cd ecommerce-api-legacy
   npm install
   npm start
   # Em outro terminal:
   curl -i http://localhost:3000/health
   curl -i http://localhost:3000/api/courses
   ```

3. **Testar `task-manager-api` (Python)**:
   ```bash
   cd task-manager-api
   python -m unittest tests/test_api.py # ou pytest
   python app.py
   # Em outro terminal:
   curl -i http://localhost:5000/health
   curl -i http://localhost:5000/tasks
   ```
