# 🚀 Refactor-Arch: Skill para Refatoração Arquitetural Automatizada

Bem-vindo ao **refactor-arch**, uma *skill* customizada para o Claude Code CLI desenvolvida para analisar, auditar e refatorar autonomamente projetos legados em direção a uma arquitetura limpa e desacoplada no padrão **MVC (Model-View-Controller)**, suportando diferentes stacks tecnológicas (`Python/Flask` e `Node.js/Express`).

## 📂 Estrutura do Repositório

O ambiente contém a raiz do repositório com três subprojetos legados, além dos arquivos de configuração da *skill*:

```text
mba-ia-refactor-projects-skill/
├── .claude/
│   └── skills/
│       └── refactor-arch/
│           ├── SKILL.md                     # Orquestração principal da skill (Fases 1, 2 e 3)
│           ├── analise_heuristica.md        # Heurísticas de detecção e mapeamento inicial
│           ├── catalogo_anti_patterns.md    # Catálogo de débitos técnicos e anti-patterns
│           ├── guideline_arquitetura_mvc.md # Blueprint da arquitetura MVC alvo
│           ├── template_relatorio.md        # Template oficial para relatórios de auditoria
│           └── playbook_refatoracao.md      # Playbook de Refatoração (Exemplos Antes vs. Depois)
├── code-smells-project/                # Python / Flask 3.1.1 (API E-Commerce - SQL nativo / Alto acoplamento)
├── ecommerce-api-legacy/               # Node.js / Express 4.18 (LMS API - God Class / BD em memória)
└── task-manager-api/                   # Python / Flask 3.0 / SQLAlchemy (Task Manager - Parcialmente organizado)
```

---

## 🔍 Seção A: Análise Manual

Antes da construção do motor da *skill*, realizamos uma auditoria manual detalhada em cada um dos três repositórios legados. Identificamos 5 problemas centrais por projeto (com severidades `CRITICAL`/`HIGH`, `MEDIUM` e `LOW`), priorizando aspectos de alto impacto arquitetural e de segurança.

### 1. `code-smells-project/` (Python / Flask — API de E-commerce)
* **[CRITICAL] SQL Injection & Interpolação Direta:** Consultas SQL montadas por interpolação de strings diretamente nas rotas HTTP.
  * *Justificativa:* Risco altíssimo de vazamento ou destruição de dados do e-commerce por injeção maliciosa, além de impedir o reuso de lógica de acesso a dados.
* **[MEDIUM] God File (`app.py` Monolítico):** Concentração de todas as rotas de produtos, pedidos e usuários em um único arquivo de mais de 400 linhas.
  * *Justificativa:* Violação do Princípio da Responsabilidade Única (SRP), dificultando manutenção paralela e testes isolados.
* **[MEDIUM] Acoplamento de Lógica de Negócios nas Rotas:** Cálculos de desconto e totais de pedidos executados inline dentro dos handlers HTTP.
  * *Justificativa:* Impossibilita a reutilização de regras de negócio em outros fluxos ou interfaces (ex: CLI, background jobs).
* **[LOW] Tratamento Genérico e Exposição de Exceções:** Blocos `try/except Exception` retornando tracebacks brutos ou respostas `500` genéricas sem padronização.
  * *Justificativa:* Vazamento de detalhes internos da aplicação e má experiência para os clientes da API.
* **[LOW] Configurações e Strings de Conexão Hardcoded:** Parâmetros de banco de dados e credenciais definidos diretamente no código-fonte.
  * *Justificativa:* Dificulta o deploy e a transição entre ambientes (desenvolvimento, staging, produção).

### 2. `ecommerce-api-legacy/` (Node.js / Express — LMS API com Checkout)
* **[HIGH] Estado Volátil em Memória (God State / In-Memory Storage):** Cursos, matrículas e transações armazenados em objetos e arrays globais JavaScript (`let database = {}`).
  * *Justificativa:* Perda total de estado a cada reinício da aplicação, além de inviabilizar o dimensionamento horizontal (cluster/containers).
* **[MEDIUM] Ausência de Separação em Camadas (Monolito no `server.js`):** Manipuladores do Express controlando parsing HTTP, regras de checkout, cálculo de frete e alteração de estado inline.
  * *Justificativa:* Gera acoplamento extremo entre o framework web (Express) e o domínio da aplicação.
* **[MEDIUM] Falta de Sanitização e Validação de Payload:** Leitura direta de `req.body` sem checagem de schema, tipos ou campos obrigatórios.
  * *Justificativa:* Permite a inserção de dados inconsistentes ou malformados, levando a erros em tempo de execução.
* **[LOW] Inexistência de Padronização de Respostas HTTP:** Mistura de respostas JSON com objetos simples, mensagens puras em texto e status codes inconsistentes (ex: `200 OK` em erros de validação).
  * *Justificativa:* Torna a integração instável para clientes frontend ou dispositivos móveis.
* **[LOW] Falta de Logs Estruturados:** Utilização extensiva de `console.log` espalhados sem níveis de severidade (info, error, debug).
  * *Justificativa:* Dificulta a monitoria e auditoria de erros em ambientes de produção.

### 3. `task-manager-api/` (Python / Flask / SQLAlchemy — Task Manager)
* **[HIGH] Gestão Manual e Insegura de Migrações e Seeds:** População de banco executada por scripts externos soltos (`seed.py`) sem validação estrita de variáveis de ambiente (`APP_ENV`).
  * *Justificativa:* Risco de sobrescrever acidentalmente bancos de dados em ambiente de produção.
* **[MEDIUM] Acoplamento de Segurança no Controller de Tarefas:** Lógica de validação do token JWT e permissões de perfil (`role`) misturada com queries de CRUD de tarefas.
  * *Justificativa:* Dificulta a reutilização dos mecanismos de autenticação em novas rotas e contamina o escopo de tarefas.
* **[MEDIUM] Rotas Parcialmente Modularizadas com Mapeamento Misto:** Blueprints configurados de forma inconsistente, mesclando caminhos raiz e prefixados.
  * *Justificativa:* Gera confusão na navegação de endpoints e retornos `404 Not Found` inesperados durante chamadas da API.
* **[LOW] Ausência de Fallback Seguro para `SECRET_KEY`:** Geração temporária de chaves aleatórias em tempo de execução sem persistência em arquivo de ambiente.
  * *Justificativa:* Invalida todos os tokens JWT ativos dos usuários caso o processo do servidor Flask seja reiniciado.
* **[LOW] Poluição de Output com Impressões Brutas:** Mensagens de debug enviadas para o stdout via `print` em vez de loggers configurados por módulo.
  * *Justificativa:* Impede a filtragem e coleta adequada de métricas e erros.

---

## ⚙️ Seção B: Construção da Skill

* **Decisões de Design:**
  * A *skill* foi projetada com base em uma **arquitetura orientada a fases sequenciais** acionadas pelo Claude Code CLI:
    1. **Fase 1 (Análise):** Mapeamento do projeto, identificação da stack e construção do mapa de rotas (`app.url_map` / `Express Router`).
    2. **Fase 2 (Auditoria):** Varredura usando o `catalogo_anti_patterns.md` e geração do relatório `reports/audit-project-<id>.md` com stop obrigatorio.
    3. **Fase 3 (Refatoração & Validação):** Migração modular no padrão MVC e validação prática de conectividade.
  * Os arquivos de referência (`guideline_arquitetura_mvc.md`, `catalogo_anti_patterns.md`, `analise_heuristica.md`, `playbook_refatoracao.md`) foram mantidos desacoplados da instrução principal (`SKILL.md`) para economizar janela de contexto e ser consumidos sob demanda.

* **Anti-Patterns Incluídos no Catálogo:**
  * **God Class / God File:** Identifica arquivos únicos agrupando mais de uma responsabilidade.
  * **Inline Persistence / Raw Queries:** Detecta SQL nativo interpolado e armazenamento direto em memória.
  * **Cross-Layer Leakage:** Flag de regras de negócio vazando dentro da camada de apresentação/rotas.
  * **Unvalidated Input / Payload Injection:** Ausência de schemas e checagem de entradas.

* **Agnosticismo de Tecnologia:**
  * A *skill* não assume uma estrutura pré-definida de pastas. Ela inspeciona os manifestos (`requirements.txt`, `Pipfile`, `package.json`) para reconhecer o ecossistema.
  * A separação em camadas respeita a idiomática de cada linguagem (ex: Blueprints + SQLAlchemy em Flask; Routers + ORM/Data Mapper em Node.js), aplicando o padrão conceitual **MVC** de forma equivalente em ambas as stacks.

* **Desafios Encontrados e Soluções:**
  * *Desafio 1 (Divergência de Prefixo de Rotas):* Em APIs Flask, endpoints eram expostos diretamente na raiz (ex: `/tasks`) enquanto em outros projetos usavam `/api/v1`.
    * *Solução:* A skill passou a executar uma inspeção estática no mapa ativo de URLs (`app.url_map`) antes de refatorar as rotas, preservando 100% o contrato de URI original.
  * *Desafio 2 (Interpolação no PowerShell):* Testes com headers HTTP de autorização falhavam ao passar `"Bearer $token"` direto em aspas duplas no terminal Windows.
    * *Solução:* Documentamos a criação prévia da HashTable `@Headers = @{ "Authorization" = "Bearer $token" }` para garantir a execução limpa das requisições de validação.

---

## 📊 Seção C: Resultados

### 1. Resumo dos Relatórios de Auditoria

| Projeto | Linguagem / Framework | Critical | High | Medium | Low | Total Findings |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `code-smells-project` | Python / Flask | 1 | 0 | 2 | 2 | **5** |
| `ecommerce-api-legacy` | Node.js / Express | 0 | 1 | 2 | 2 | **5** |
| `task-manager-api` | Python / Flask / SQLAlchemy | 0 | 1 | 2 | 2 | **5** |

---

### 2. Comparação Antes/Depois da Estrutura de Cada Projeto

#### A. `code-smells-project/`
* **Antes:**
  ```text
  code-smells-project/
  ├── app.py                  # Monolito contendo BD, Rotas, Regras e SQL nativo
  └── requirements.txt
  ```
* **Depois:**
  ```text
  code-smells-project/
  ├── app.py                  # Ponto de entrada leve
  ├── src/
  │   ├── config/             # Configurações e conexões de BD
  │   ├── models/             # Entidades/ORM do e-commerce
  │   ├── controllers/        # Lógica de checkout e produtos
  │   └── routes/             # Blueprints das rotas HTTP
  └── requirements.txt
  ```

#### B. `ecommerce-api-legacy/`
* **Antes:**
  ```text
  ecommerce-api-legacy/
  ├── server.js               # Arquivo único com array em memória e rotas do Express
  └── package.json
  ```
* **Depois:**
  ```text
  ecommerce-api-legacy/
  ├── server.js               # Bootstrap do servidor HTTP
  ├── src/
  │   ├── models/             # Camada de abstração de dados (Data Layer)
  │   ├── controllers/        # Controladores de checkout, cursos e alunos
  │   └── routes/             # Routers desacoplados do Express
  └── package.json
  ```

#### C. `task-manager-api/`
* **Antes:**
  ```text
  task-manager-api/
  ├── app.py
  ├── seed.py
  └── src/                    # Estrutura parcial sem padronização estrita de Controllers
      ├── database.py
      └── views.py
  ```
* **Depois:**
  ```text
  task-manager-api/
  ├── app.py                  # Inicializador limpo da aplicação
  ├── seed.py                 # Script de inicialização compatível
  └── src/
      ├── config/             # Database e Seed scripts
      ├── models/             # User, Task e Category models (SQLAlchemy)
      ├── controllers/        # Auth, Task e User controllers
      └── routes/             # Auth, Task e User blueprints
  ```

---

### 3. Checklist de Validação Preenchido por Projeto

#### `code-smells-project` (Python/Flask)
- [x] Detecção de dependências e stack tecnológica efetuada.
- [x] Relatório de auditoria gerado em `reports/audit-project-code-smells.md`.
- [x] Estrutura refatorada para a pasta `src/` com suporte a MVC.
- [x] Consultas SQL parametrizadas/abstraídas via modelo.
- [x] Servidor rodando e rotas respondendo com sucesso (`200 OK`).

#### `ecommerce-api-legacy` (Node.js/Express)
- [x] Detecção do ambiente Node.js realizada.
- [x] Relatório de auditoria gerado em `reports/audit-project-ecommerce-api.md`.
- [x] Divisão em `src/models`, `src/controllers` e `src/routes`.
- [x] Contrato das rotas HTTP originais preservado.
- [x] Aplicação inicializada com `npm start` e validada funcionalmente.

#### `task-manager-api` (Python/Flask/SQLAlchemy)
- [x] Mapeamento de rotas verificado via `app.url_map`.
- [x] Relatório de auditoria gerado em `reports/audit-project-task-manager.md`.
- [x] Migração para arquitetura limpa em `src/` concluída.
- [x] Fluxo completo de autenticação JWT (`POST /login`) testado com sucesso.
- [x] Requisições autenticadas em rotas protegidas (`GET /tasks`) validadas com retorno de dados (`200 OK`).

---

### 4. Evidências de Execução e Logs (`task-manager-api`)

**Inicialização do Servidor e População de Banco (Seed):**
```powershell
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> $env:APP_ENV="development"
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> $env:SEED_ADMIN_PASSWORD="minhasenhasegura"
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> python seed.py --reset
2026-11-10 21:34:46,708 INFO src.config.seed: Seed concluído: 3 usuários, 4 categorias, 10 tasks
```

**Autenticação JWT e Consulta Autenticada no Endpoint Refatorado (`GET /tasks`):**
```powershell
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> $response = Invoke-RestMethod -Uri "http://localhost:5000/login" -Method Post -ContentType "application/json" -Body '{"email": "joao@email.com", "password": "minhasenhasegura"}'
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> $token = $response.token
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> $headers = @{ "Authorization" = "Bearer $token" }
(venv) PS C:\projetos\mba-ia-refactor-projects-skill\task-manager-api> Invoke-RestMethod -Uri "http://localhost:5000/tasks" -Method Get -Headers $headers

id            : 1
title         : Implementar autenticação JWT
description   : Adicionar autenticação real com JWT
status        : pending
user_name     : João Silva
category_name : Backend
...
```

---

### 5. Comportamento da Skill em Stacks Diferentes
A *skill* provou ser agnóstica de stack ao adaptar a lógica de refatoração conforme o ecossistema:
* **No Python/Flask:** Utilizou a API de `Blueprints` do Flask para a camada de rotas, encapsulou lógica em instâncias de Controllers Python e manteve o ORM `SQLAlchemy`.
* **No Node.js/Express:** Organizou os arquivos utilizando o `express.Router()`, exportou funções controladoras assíncronas (`async/await`) e isolou os dados em módulos Data Access Objects / Models em JavaScript.

---

## 🏃 Seção D: Como Executar

### 1. Pré-requisitos
* **Node.js:** `v18.0.0` ou superior.
* **Python:** `3.10+` com ambiente virtual (`venv`).
* **Claude Code CLI:** Instalado e autenticado.
  ```bash
  npm install -g @anthropic-ai/claude-code
  claude login
  ```

---

### 2. Comandos para Executar a Skill em Cada Projeto

Navegue até o repositório principal ou entra diretamente na pasta do subprojeto desejado antes de chamar a skill no Claude Code CLI:

#### A. No projeto `code-smells-project`:
```bash
cd code-smells-project
claude "/refactor-arch"
```

#### B. No projeto `ecommerce-api-legacy`:
```bash
cd ecommerce-api-legacy
claude "/refactor-arch"
```

#### C. No projeto `task-manager-api`:
```bash
cd task-manager-api
claude "/refactor-arch"
```

---

### 3. Como Validar que a Refatoração Funcionou

#### Para Projetos Python / Flask (`code-smells-project` e `task-manager-api`):
1. Ative o ambiente virtual e instale as dependências:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. (Se aplicável) Popule o banco de dados:
   ```powershell
   $env:APP_ENV="development"
   python seed.py --reset
   ```
3. Inicie a aplicação:
   ```powershell
   python app.py
   ```
4. Teste as chamadas nos endpoints da API utilizando o PowerShell:
   ```powershell
   # Obter Token
   $res = Invoke-RestMethod -Uri "http://localhost:5000/login" -Method Post -ContentType "application/json" -Body '{"email":"joao@email.com","password":"minhasenhasegura"}'
   # Consumir endpoint protegido
   $headers = @{ "Authorization" = "Bearer $($res.token)" }
   Invoke-RestMethod -Uri "http://localhost:5000/tasks" -Method Get -Headers $headers
   ```

#### Para Projetos Node.js / Express (`ecommerce-api-legacy`):
1. Instale as dependências:
   ```bash
   npm install
   ```
2. Inicie a aplicação:
   ```bash
   npm start
   ```
3. Teste os endpoints via terminal:
   ```bash
   curl http://localhost:3000/health
   curl http://localhost:3000/products
   ```