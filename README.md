# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
codex '$refactor-arch'
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Ferramenta escolhida:** OpenAI Codex, com a skill instalada em `.codex/skills/refactor-arch/` dentro de cada projeto.

## Análise Manual

A análise abaixo considera o código original dos três projetos, antes da execução da skill ou de qualquer refatoração. Os findings estão ordenados da maior para a menor severidade e usam a escala definida neste documento.

### `code-smells-project`

Resumo: **7 findings** — 2 CRITICAL, 1 HIGH, 2 MEDIUM e 2 LOW.

#### [CRITICAL] Endpoint permite executar SQL arbitrário

- **Evidência:** `code-smells-project/app.py:59-78`
- **Problema:** a rota pública `POST /admin/query` aceita o campo `sql` da requisição e o entrega diretamente a `cursor.execute()`, sem autenticação, autorização ou restrição do tipo de comando.
- **Relevância:** qualquer cliente pode ler, alterar ou apagar todo o banco de dados. A falha compromete confidencialidade, integridade e disponibilidade dos dados.

#### [CRITICAL] SQL Injection e armazenamento de senhas em texto puro

- **Evidência:** `code-smells-project/models.py:105-131` e `code-smells-project/database.py:75-83`
- **Problema:** cadastro e login montam SQL por concatenação; a senha é comparada e persistida sem hash. A carga inicial também contém credenciais em texto puro.
- **Relevância:** entradas manipuladas podem alterar a consulta de autenticação, e um vazamento do banco expõe imediatamente todas as senhas dos usuários.

#### [HIGH] Estado global de banco compartilhado entre requisições

- **Evidência:** `code-smells-project/database.py:4-11`
- **Problema:** uma única conexão SQLite global é reutilizada com `check_same_thread=False`, sem ciclo de vida por requisição e sem sincronização.
- **Relevância:** requisições concorrentes podem compartilhar transações e cursores de forma imprevisível, dificultando isolamento, testes e recuperação segura de erros.

#### [MEDIUM] Consultas N+1 na leitura de pedidos

- **Evidência:** `code-smells-project/models.py:171-233`
- **Problema:** depois de buscar os pedidos, o código consulta itens para cada pedido e produtos para cada item.
- **Relevância:** o número de acessos ao banco cresce com a quantidade de pedidos e itens, causando degradação progressiva de latência e capacidade.

#### [MEDIUM] Validação e regras de negócio duplicadas nos controllers

- **Evidência:** `code-smells-project/controllers.py:24-96`
- **Problema:** criação e atualização repetem leitura do payload, validações e mensagens, enquanto regras de produto ficam acopladas à camada HTTP.
- **Relevância:** mudanças de regra precisam ser replicadas em vários fluxos e podem produzir comportamentos divergentes, além de dificultar testes isolados.

#### [LOW] Valores operacionais e regras numéricas estão espalhados no código

- **Evidência:** `code-smells-project/app.py:7-8`, `code-smells-project/app.py:88` e `code-smells-project/models.py:256-262`
- **Problema:** chave secreta, modo debug, porta, faixas de faturamento e percentuais de desconto são literais sem configuração centralizada ou nomes de domínio.
- **Relevância:** isso reduz legibilidade e exige alteração de código para adaptar o ambiente ou as regras comerciais.

#### [LOW] Uso de `print` como logging de aplicação

- **Evidência:** `code-smells-project/controllers.py:8-12`, `code-smells-project/controllers.py:57-61` e `code-smells-project/app.py:83-86`
- **Problema:** eventos e erros são enviados diretamente para a saída padrão, sem nível, contexto estruturado ou correlação de requisição.
- **Relevância:** a observabilidade fica inconsistente e torna incidentes mais demorados de diagnosticar.

### `ecommerce-api-legacy`

Resumo: **7 findings** — 2 CRITICAL, 1 HIGH, 2 MEDIUM e 2 LOW.

#### [CRITICAL] Credenciais e chave de pagamento estão hardcoded

- **Evidência:** `ecommerce-api-legacy/src/utils.js:1-6`
- **Problema:** usuário e senha do banco, chave marcada como `live` do gateway e usuário SMTP ficam versionados no código-fonte.
- **Relevância:** quem obtiver acesso ao repositório também obtém acesso aos serviços externos; a exposição exige rotação imediata dos segredos.

#### [CRITICAL] Função de senha usa Base64 truncado em vez de hash seguro

- **Evidência:** `ecommerce-api-legacy/src/utils.js:17-22` e `ecommerce-api-legacy/src/AppManager.js:66-70`
- **Problema:** `badCrypto` repete uma codificação reversível e retorna somente dez caracteres; quando a senha não é informada, o checkout ainda adota a senha padrão `123456`.
- **Relevância:** credenciais podem ser recuperadas ou descobertas com baixo custo, permitindo tomada de contas.

#### [HIGH] `AppManager` concentra rotas, negócio, persistência e infraestrutura

- **Evidência:** `ecommerce-api-legacy/src/AppManager.js:4-138`
- **Problema:** a mesma classe cria o schema e os dados iniciais, registra endpoints, processa pagamento, matricula usuários, gera relatórios e remove dados.
- **Relevância:** a violação de responsabilidade única cria forte acoplamento com Express e SQLite, impedindo testes isolados e tornando qualquer mudança arriscada.

#### [MEDIUM] Checkout não possui transação atômica

- **Evidência:** `ecommerce-api-legacy/src/AppManager.js:43-63`
- **Problema:** matrícula, pagamento e auditoria são gravados em callbacks independentes, sem `BEGIN`, `COMMIT` e `ROLLBACK` abrangendo a operação completa.
- **Relevância:** uma falha intermediária pode deixar matrícula sem pagamento ou checkout sem log, corrompendo a consistência do fluxo financeiro.

#### [MEDIUM] Relatório financeiro executa consultas N+1 aninhadas

- **Evidência:** `ecommerce-api-legacy/src/AppManager.js:80-128`
- **Problema:** para cada curso são buscadas matrículas e, para cada matrícula, usuário e pagamento em consultas separadas.
- **Relevância:** o volume de consultas cresce rapidamente com os dados e aumenta a latência e o risco de falhas no endpoint administrativo.

#### [LOW] Nomes abreviados escondem o significado dos dados

- **Evidência:** `ecommerce-api-legacy/src/AppManager.js:28-35`
- **Problema:** variáveis como `u`, `e`, `p`, `cid` e `cc`, além de campos como `usr`, `eml` e `c_id`, não comunicam claramente seu papel.
- **Relevância:** a leitura e a revisão do fluxo sensível de checkout ficam mais lentas e sujeitas a enganos.

#### [LOW] Erro de exclusão é ignorado e a resposta afirma sucesso

- **Evidência:** `ecommerce-api-legacy/src/AppManager.js:131-136`
- **Problema:** o callback recebe `err`, mas não o verifica; a rota sempre responde que o usuário foi removido.
- **Relevância:** clientes podem receber falso sucesso, enquanto a aplicação perde informação útil para diagnóstico e recuperação.

### `task-manager-api`

Resumo: **7 findings** — 2 CRITICAL, 1 HIGH, 2 MEDIUM e 2 LOW.

#### [CRITICAL] Hash de senha é exposto nas respostas da API

- **Evidência:** `task-manager-api/models/user.py:16-24`, `task-manager-api/routes/user_routes.py:33-40` e `task-manager-api/routes/user_routes.py:207-210`
- **Problema:** `User.to_dict()` inclui `password`, e esse serializador é usado em respostas de cadastro, consulta, atualização e login.
- **Relevância:** qualquer consumidor desses endpoints obtém hashes de senha, ampliando o impacto de acesso indevido e permitindo ataques offline.

#### [CRITICAL] Senhas usam MD5 sem salt

- **Evidência:** `task-manager-api/models/user.py:27-32`
- **Problema:** criação e verificação de senha aplicam MD5 diretamente, um algoritmo rápido, obsoleto para armazenamento de credenciais e sem salt individual.
- **Relevância:** hashes vazados são vulneráveis a rainbow tables e força bruta de alta velocidade; deve ser usado um password hasher adaptativo, como Argon2 ou bcrypt.

#### [HIGH] Autenticação e autorização são apenas simuladas

- **Evidência:** `task-manager-api/routes/user_routes.py:185-210` e `task-manager-api/routes/task_routes.py:11-12`
- **Problema:** o login retorna um token previsível no formato `fake-jwt-token-<id>`, e as rotas de tarefas e usuários não validam token nem papel.
- **Relevância:** qualquer cliente pode acessar e alterar recursos sem identidade confiável ou controle de permissão.

#### [MEDIUM] Listagem de tarefas executa consultas N+1

- **Evidência:** `task-manager-api/routes/task_routes.py:14-59`
- **Problema:** a rota carrega todas as tarefas e faz buscas adicionais de usuário e categoria dentro do loop.
- **Relevância:** uma listagem pode executar duas consultas extras por tarefa, degradando o tempo de resposta conforme a base cresce.

#### [MEDIUM] Regras de validação e serialização estão duplicadas

- **Evidência:** `task-manager-api/routes/task_routes.py:85-144`, `task-manager-api/routes/task_routes.py:156-215` e `task-manager-api/utils/helpers.py:57-115`
- **Problema:** criação e atualização repetem validações que também existem em `process_task_data`; constantes declaradas no helper não são usadas pelas rotas.
- **Relevância:** regras duplicadas tendem a divergir, aumentando defeitos e custo de manutenção.

#### [LOW] Imports não utilizados geram ruído

- **Evidência:** `task-manager-api/app.py:7`, `task-manager-api/routes/task_routes.py:7` e `task-manager-api/utils/helpers.py:3-7`
- **Problema:** módulos como `sys`, `json`, `os`, `time`, `math` e `hashlib` são importados sem uso nos respectivos arquivos.
- **Relevância:** o ruído reduz a clareza sobre dependências reais e dificulta revisões e ferramentas de análise estática.

#### [LOW] Exceções genéricas são silenciadas

- **Evidência:** `task-manager-api/routes/task_routes.py:62-63`, `task-manager-api/routes/user_routes.py:127-132` e `task-manager-api/utils/helpers.py:43-50`
- **Problema:** blocos `except:` capturam qualquer exceção sem registrar tipo, mensagem ou stack trace.
- **Relevância:** erros de programação podem parecer falhas comuns de entrada ou banco, reduzindo a capacidade de diagnóstico.

## Construção da Skill

A implementação escolhida usa a convenção do OpenAI Codex: cada projeto contém `.codex/skills/refactor-arch/SKILL.md` e cinco referências Markdown. O workflow é sequencial e auditável:

1. a Fase 1 descobre unidades executáveis, stack, domínio, arquitetura, contratos e comandos sem modificar a codebase;
2. a Fase 2 cruza evidências com o catálogo, salva o relatório em `reports/` e interrompe a execução no checkpoint humano;
3. somente uma autorização posterior libera a Fase 3, que aplica o plano aprovado em ondas pequenas e valida sintaxe, dependências, testes, boot, contratos e escopo do diff.

As decisões de design mais importantes foram preservar contratos públicos, separar fatos de inferências, registrar paths/linhas e usar MVC como papéis arquiteturais, não como nomes rígidos de pastas. Em HTTP, Routes/Views traduzem o protocolo, Controllers orquestram casos de uso e Models/domínio protegem estado e invariantes; repositories e integrações ficam em infraestrutura, enquanto o entry point apenas compõe as dependências.

O catálogo possui 14 anti-patterns e o playbook possui 11 transformações com exemplos antes/depois:

| Grupo | Anti-patterns | Por que foi incluído |
|---|---|---|
| Segurança | AP-01 injection; AP-02 segredo/dado sensível; AP-03 autenticação/criptografia | Os três projetos tinham superfícies públicas ou credenciais inseguras com impacto direto em dados e contas. |
| Arquitetura e integridade | AP-04 God component; AP-05 fat adapter; AP-06 estado global; AP-07 falta de atomicidade | São as causas principais de acoplamento, testes frágeis e estado parcial nos projetos legados. |
| Qualidade operacional | AP-08 N+1; AP-09 duplicação; AP-10 erros inadequados | Permitem detectar degradação de performance, regras divergentes e falso sucesso. |
| Evolução | AP-11 APIs deprecated | Evita modernização por memória: exige versão efetiva, fonte primária e substituto comprovado. |
| Integrações e manutenção | AP-12 I/O frágil; AP-13 configuração dispersa; AP-14 higiene | Cobre timeouts, segredos/configuração externa, observabilidade, código morto e legibilidade. |

A skill permaneceu agnóstica de tecnologia porque descobre manifests, entry points, interfaces, persistência e comandos a partir dos artefatos locais. O mesmo roteiro foi aplicado a Flask com SQLite direto, Express com `node:sqlite` e Flask-SQLAlchemy, adaptando “Model”, “View” e “Controller” às convenções de cada stack.

Os principais desafios foram preservar contratos enquanto se corrigiam falhas de segurança, validar sem tocar bancos reais e substituir dependências legadas. A solução foi registrar as mudanças de segurança no plano aprovado, usar bancos/portas temporários e test doubles, manter adapters de compatibilidade quando necessário e executar contract tests após cada refatoração.

## Resultados

Os relatórios de auditoria foram preservados como histórico das Fases 1–2 e receberam apenas metadados corrigidos e evidências da Fase 3:

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---:|---:|---:|---:|---:|---|
| `code-smells-project` | 5 | 5 | 3 | 2 | 15 | [`audit-project-1.md`](reports/audit-project-1.md) |
| `ecommerce-api-legacy` | 1 | 6 | 4 | 1 | 12 | [`audit-project-2.md`](reports/audit-project-2.md) |
| `task-manager-api` | 3 | 4 | 5 | 2 | 14 | [`audit-project-3.md`](reports/audit-project-3.md) |

### Comparação antes/depois

| Projeto | Antes | Depois |
|---|---|---|
| `code-smells-project` | Quatro módulos Python com SQL, HTTP, domínio, configuração e estado global atravessando camadas nominais. | `store/domain`, `store/controllers`, `store/views` e `store/infrastructure`, com ports de domínio, configuração externa e `app.py` como composition root. |
| `ecommerce-api-legacy` | Três fontes JavaScript; `AppManager` concentrava rotas, schema, negócio, SQL e relatórios. | `domain`, `application`, `adapters/http`, `infrastructure` e `config`; `src/app.js` injeta dependências e controla lifecycle. |
| `task-manager-api` | Pastas nominais, mas routes concentravam queries, validação, negócio e apresentação; bootstrap tinha efeitos. | Routes finas, Controllers, repositories, schemas, Models, services e errors; application factory sem criar schema no import e seed CLI transacional. |

### Checklist de validação

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|:---:|:---:|:---:|
| Linguagem, framework e domínio detectados | ✅ | ✅ | ✅ |
| Contagem original de fontes validada | 5 | 6 | 16 |
| Relatório ordenado, com paths/linhas e checagem deprecated | ✅ | ✅ | ✅ |
| Pelo menos 5 findings e 1 CRITICAL/HIGH | 15 / ✅ | 12 / ✅ | 14 / ✅ |
| MVC/equivalente, configuração, Models, Routes e Controllers | ✅ | ✅ | ✅ |
| Error handling e entry point centralizados | ✅ | ✅ | ✅ |
| Sintaxe/dependências | ✅ | ✅ | ✅ |
| Testes automatizados | 13/13 | 16/16 | 16/16 |
| Boot/readiness e encerramento limpo | ✅ | ✅ | ✅ |
| Contratos originais | 19/19 | 3/3 | 22/22 HTTP + seed CLI |

### Logs da validação pós-refatoração

```text
code-smells-project
  pip check: No broken requirements found
  unittest: Ran 13 tests — OK
  boot: readiness HTTP em porta temporária — PASS
  contracts: 19 métodos/paths, 20 requisições reais — PASS

ecommerce-api-legacy
  node --check: src/ e tests/ — PASS
  node --test: 16 tests, 16 pass, 0 fail
  boot/shutdown: load-ok; boot-close-ok
  smoke: checkout 200; impersonação 403; relatório 200; DELETE protegido 409

task-manager-api
  pip check: No broken requirements found
  unittest: Ran 16 tests — OK
  boot: readiness HTTP e shutdown limpo — PASS
  contracts: 22/22 operações HTTP; seed CLI exit 0 — PASS
```

No Flask com SQLite direto, a maior adaptação foi introduzir ports e ciclo de vida de conexão. No Express, foram usados casos de uso funcionais e `node:sqlite`. No Flask-SQLAlchemy, a estrutura parcial foi preservada e completada com Controllers, repositories, schemas e autorização por papel. Isso demonstra reutilização do mesmo workflow sem impor uma árvore específica a todas as stacks.

O fork público destinado à entrega está em [matheus-santos-souza/mba-ia-refactor-projects-skill](https://github.com/matheus-santos-souza/mba-ia-refactor-projects-skill), derivado do repositório base `devfullcycle/mba-ia-refactor-projects-skill`. O estado validado descrito aqui é publicado por uma branch de entrega e submetido por pull request para a branch `dev` do fork.

## Como Executar

### Pré-requisitos

- OpenAI Codex CLI instalado e autenticado;
- Python 3.12 ou superior para os projetos 1 e 3;
- Node.js 22.5 ou superior para o projeto 2;
- dependências instaladas conforme o README de cada projeto;
- segredos apenas de teste definidos pelas variáveis documentadas nos arquivos `.env.example` ou nos READMEs locais.

Cada projeto contém sua própria cópia da skill. Execute as Fases 1–2 e encerre no checkpoint:

```bash
cd code-smells-project
codex '$refactor-arch Execute as Fases 1 e 2 e salve o relatório em ../reports/audit-project-1.md'

cd ../ecommerce-api-legacy
codex '$refactor-arch Execute as Fases 1 e 2 e salve o relatório em ../reports/audit-project-2.md'

cd ../task-manager-api
codex '$refactor-arch Execute as Fases 1 e 2 e salve o relatório em ../reports/audit-project-3.md'
```

Depois de revisar cada relatório, autorize a Fase 3 em uma nova execução explícita. Exemplo para o projeto 1:

```bash
codex '$refactor-arch Autorizo a Fase 3 conforme ../reports/audit-project-1.md'
```

Repita o comando nos outros projetos, alterando apenas o nome do relatório. Para validar a entrega atual sem refatorar novamente:

```bash
# Projeto 1
cd code-smells-project
APP_SECRET='segredo-de-teste-com-pelo-menos-32-caracteres' \
  .venv/bin/python -m unittest discover -s tests -v

# Projeto 2
cd ../ecommerce-api-legacy
npm test

# Projeto 3
cd ../task-manager-api
.venv/bin/python -m unittest discover -s tests -v
```

O boot manual e as variáveis obrigatórias estão documentados em [`code-smells-project/README.md`](code-smells-project/README.md), [`ecommerce-api-legacy/README.md`](ecommerce-api-legacy/README.md) e [`task-manager-api/README.md`](task-manager-api/README.md). A refatoração está validada quando os testes terminam sem falhas, o processo atinge readiness sem criar dados fora do ambiente temporário e os contract tests confirmam todos os métodos, paths, status e shapes esperados.
