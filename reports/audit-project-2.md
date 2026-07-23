# Architecture Audit Report — ecommerce-api-legacy

## Fase 1 — análise do projeto

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language(s):   JavaScript CommonJS
Runtime(s):    Node.js; versão exata UNKNOWN
Framework(s):  Express 4.22.1; sqlite3 5.1.7
Dependencies:  Express e sqlite3
Persistence:   SQLite em memória; schema e seeds criados no boot; cache global
Domain:        LMS/e-commerce: usuários, cursos, matrículas, pagamentos e relatório financeiro
Architecture:  Monólito procedural; God class com handlers, regras e SQL acoplados
Entry points:  src/app.js; npm start → node src/app.js
Source files:  6 artefatos técnicos; 3 fontes JavaScript, 180 linhas
Contracts:     3 interfaces HTTP
Tests:         Ausentes; api.http contém apenas chamadas manuais
================================
```

Existe uma única unidade executável. Foram considerados:

- `src/app.js`, `src/AppManager.js`, `src/utils.js`;
- `package.json`, `package-lock.json`;
- `api.http`.

`README.md` foi usado como evidência secundária. `node_modules`, seus binários, caches, cobertura e metadados de instalação foram excluídos.

## Metadata

- **Codebase root:** `/home/matheussouza/learn/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
- **Delivery repository root:** `/home/matheussouza/learn/mba-ia-refactor-projects-skill`
- **Version-control snapshot:** `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- **Audited source fingerprint:** tree `a24d7a58b0b1fdd3b57a456a576aff7069a15f22` em `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- **Preexisting changes:** nenhum arquivo alterado dentro do escopo
- **Audited at:** `2026-07-22T20:15:54-04:00`
- **Scope:** `src/**/*.js`, `package.json`, `package-lock.json`, `api.http`; README como evidência secundária
- **Exclusions:** `node_modules/**` e respectivos artefatos gerados
- **Source files:** 6 artefatos técnicos; 3 fontes JavaScript
- **Lines inspected:** 180 linhas JavaScript; metadados pertinentes dos demais artefatos
- **Report path:** `reports/audit-project-2.md`
- **Phase 1–2 filesystem changes:** este relatório somente

## Project Analysis

| Atributo | Resultado | Evidência | Confiança |
|---|---|---|---|
| Linguagem/runtime | JavaScript CommonJS sobre Node.js; versão do Node desconhecida | `package.json:5-8`, `src/app.js:1-3` | HIGH |
| Dependências | npm; Express 4.22.1 e sqlite3 5.1.7 resolvidos | `package.json:9-12`, `package-lock.json:641-644,2021-2025` | HIGH |
| Framework/interfaces | Servidor Express com três endpoints HTTP | `src/app.js:5-12`, `src/AppManager.js:28,80,131` | HIGH |
| Persistência | SQLite `:memory:`, SQL direto por callbacks, schema/seeds no boot | `src/AppManager.js:7-22` | HIGH |
| Domínio | LMS/e-commerce de usuários, cursos, matrículas, pagamentos e relatório | `src/AppManager.js:12-21,28-137` | HIGH |
| Arquitetura atual | Monólito procedural com classe central e handlers gordos | `src/AppManager.js:4-138` | HIGH |
| Unidade/entry point | Uma API; `npm start` executa `node src/app.js` | `package.json:5-8` | HIGH |
| Testes | Nenhum framework, script ou teste automatizado | `package.json:6-8`, `api.http:1-31` | HIGH |

Comandos descobertos, mas não executados:

| Categoria | Comando | Estado |
|---|---|---|
| Instalação | `npm install` | DISCOVERED |
| Restore determinístico | `npm ci` | INFERRED |
| Boot | `npm start` | DISCOVERED |
| Boot expandido | `node src/app.js` | DISCOVERED |
| Build/lint/tipos/testes | nenhum | Ausente |

## Public Contract Baseline

| Tipo | Identidade | Local | Entrada/autenticação | Saída, erro e efeito |
|---|---|---|---|---|
| HTTP | `POST /api/checkout` | `src/AppManager.js:28-78` | JSON com `usr`, `eml`, `c_id`, `card`; `pwd` opcional; sem autenticação | `200` JSON `{msg,enrollment_id}`; erros textuais `400/404/500`; pode criar usuário, matrícula, pagamento, auditoria e cache |
| HTTP | `GET /api/admin/financial-report` | `src/AppManager.js:80-129` | Sem entrada e sem autenticação | `200` array `{course,revenue,students}`; `500` textual na consulta inicial; somente leitura |
| HTTP destrutivo | `DELETE /api/users/:id` | `src/AppManager.js:131-136` | `id` textual; sem autenticação | `200` textual mesmo diante de erro; exclui apenas o usuário e deixa relações órfãs |

## Summary

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 1 |
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 1 |
| **Total** | **12** |

**Acceptance check:** `>= 5 findings`: PASS; `>= 1 CRITICAL/HIGH`: PASS.

## Deprecated API Check

- **Status:** uma dependência direta deprecated confirmada; nenhuma API Express obsoleta confirmada no código first-party.
- **Versões verificadas:** Express `4.22.1`; sqlite3 `5.1.7`; Node.js `UNKNOWN`.
- **Prova:** o projeto oficial agora identifica `node-sqlite3` como deprecated e sem manutenção. O lockfile também contém dependências transitivas com warnings de descontinuação. [Repositório oficial do node-sqlite3](https://github.com/TryGhost/node-sqlite3)
- **Substituto condicionado:** `node:sqlite`, disponível desde Node `22.5.0`, caso o baseline confirme runtime compatível; caso contrário, outro driver mantido deverá ser aprovado. [Documentação oficial do Node.js](https://nodejs.org/download/release/v22.13.0/docs/api/sqlite.html)
- **Candidatos não contados:** warnings transitivos de `prebuild-install`, `tar`, `glob`, `rimraf` e outros foram agregados à causa raiz da dependência `sqlite3`, não transformados em findings artificiais.
- Os usos atuais de `res.status`, `res.send`, `res.json` e middleware JSON aparecem na API oficial do Express 4; não houve ocorrência deprecated comprovada. [Express 4 API](https://expressjs.com/en/4x/api/)

## Findings

### F-001 — [CRITICAL] Cartão e credencial são enviados integralmente ao log

- **Catalog rule:** AP-02 — segredo ou dado sensível exposto
- **Location:** `src/AppManager.js:28-33,43-46`
- **Evidence:** o cartão vindo do body e uma chave configurada são interpolados em `console.log`; valores omitidos deste relatório.
- **Impact:** PAN e credenciais podem permanecer em stdout e agregadores de log, viabilizando fraude ou acesso indevido.
- **Recommendation:** nunca registrar PAN ou segredo; usar redaction e um adapter de pagamento tokenizado.
- **Transformation:** T01/T10
- **Validation:** enviar cartão identificável em teste e confirmar sua ausência nos logs.
- **Confidence:** HIGH

### F-002 — [HIGH] Segredos e configuração operacional estão no código-fonte

- **Catalog rule:** AP-02/AP-13
- **Location:** `src/utils.js:1-7`
- **Evidence:** senha de banco, chave com semântica live e identidade SMTP aparecem como literais; porta também exige edição de fonte.
- **Impact:** exposição em repositório/artefato, rotação difícil e implantação dependente de alteração no código. A validade externa não foi comprovada.
- **Recommendation:** remover literais, validar configuração por ambiente e rotacionar valores se forem reais.
- **Transformation:** T01
- **Validation:** busca por literais sensíveis e testes de boot com configuração válida, ausente e inválida.
- **Confidence:** HIGH

### F-003 — [HIGH] Operações privilegiadas e identidade de checkout não são autenticadas

- **Catalog rule:** AP-03 — autenticação/autorização insegura
- **Location:** `src/app.js:5-10`; `src/AppManager.js:40-75,80-135`
- **Evidence:** o único middleware global faz parsing JSON; qualquer cliente pode consultar relatório, excluir usuários ou reutilizar uma conta apenas informando o e-mail.
- **Impact:** leitura financeira indevida, deleção de usuários e operação em nome de terceiros.
- **Recommendation:** autenticação verificada e autorização administrativa explícita; vincular checkout à identidade autenticada.
- **Transformation:** T09
- **Validation:** chamadas anônimas devem falhar e credenciais autorizadas devem manter os fluxos aprovados.
- **Confidence:** HIGH
- **Contract note:** aplicar autenticação muda o contrato observado e exige aprovação explícita.

### F-004 — [HIGH] Senhas são armazenadas com transformação reversível e default previsível

- **Catalog rule:** AP-03 — criptografia insegura
- **Location:** `src/AppManager.js:12,18,68-71`; `src/utils.js:17-22`
- **Evidence:** seed em texto puro; novas senhas usam Base64 determinístico, truncado e sem salt, com senha default.
- **Impact:** credenciais são recuperáveis e contas criadas sem senha compartilham o mesmo segredo.
- **Recommendation:** usar `scrypt`, Argon2id ou bcrypt com salt; exigir senha válida e corrigir seeds.
- **Transformation:** T09
- **Validation:** hashes diferentes para a mesma senha, verificação válida e ausência de plaintext/default.
- **Confidence:** HIGH

### F-005 — [HIGH] Checkout grava estado sem transação

- **Catalog rule:** AP-07 — operação não atômica
- **Location:** `src/AppManager.js:50-61,66-72`
- **Evidence:** usuário, matrícula, pagamento e auditoria são gravados sequencialmente, sem `BEGIN`, rollback ou compensação.
- **Impact:** falhas intermediárias deixam usuário ou matrícula sem o restante do checkout.
- **Recommendation:** delimitar uma transação e produzir cache/resposta somente depois do commit.
- **Transformation:** T06
- **Validation:** fault injection após cada write deve deixar o banco no estado anterior.
- **Confidence:** HIGH

### F-006 — [HIGH] Exclusão quebra integridade referencial

- **Catalog rule:** AP-07 — integridade quebrada
- **Location:** `src/AppManager.js:12-16,131-136`
- **Evidence:** não existem foreign keys; a deleção remove apenas `users` e a resposta reconhece os dados órfãos.
- **Impact:** relatório referencia usuário inexistente e matrículas/pagamentos órfãos se acumulam.
- **Recommendation:** definir FKs e política aprovada de `CASCADE` ou `RESTRICT`, com transação.
- **Transformation:** T06
- **Validation:** verificar efeitos sobre todas as relações e rollback diante de falha.
- **Confidence:** HIGH
- **Contract note:** corrigir o efeito e a mensagem do `DELETE` constitui mudança contratual explícita.

### F-007 — [HIGH] God class e handlers HTTP gordos

- **Catalog rule:** AP-04/AP-05
- **Location:** `src/AppManager.js:4-138`
- **Evidence:** a mesma classe cria banco/schema, carrega seeds, registra rotas, valida, decide pagamento, executa SQL, agrega relatório e produz respostas.
- **Impact:** regras não podem ser testadas sem Express e SQLite; qualquer mudança possui alto raio de regressão.
- **Recommendation:** separar domínio, casos de uso/controllers, repositories, adapters HTTP e bootstrap.
- **Transformation:** T03/T04
- **Validation:** casos de uso testáveis com ports/fakes e entry point limitado à composição.
- **Confidence:** HIGH

### F-008 — [MEDIUM] Estado global e ciclo de vida das dependências são ocultos

- **Catalog rule:** AP-06
- **Location:** `src/utils.js:9-15,25`; `src/AppManager.js:5-8`; `src/app.js:8-13`
- **Evidence:** cache singleton sem limite/limpeza; banco concreto criado internamente e sem fechamento visível.
- **Impact:** estado vaza entre requests/testes, cache cresce e recursos não são substituíveis.
- **Recommendation:** injetar database/cache, definir lifecycle e encerramento limpo.
- **Transformation:** T04/T05
- **Validation:** duas instâncias isoladas, cache com política definida e teste de shutdown.
- **Confidence:** HIGH

### F-009 — [MEDIUM] Relatório executa consultas N+1

- **Catalog rule:** AP-08
- **Location:** `src/AppManager.js:83-106`
- **Evidence:** consulta cursos; para cada curso consulta matrículas; para cada matrícula consulta usuário e pagamento.
- **Impact:** total aproximado `1 + C + 2E`, aumentando latência e carga com o volume.
- **Recommendation:** consulta agregada/join ou carregamento em lote.
- **Transformation:** T07
- **Validation:** instrumentar quantidade de queries com diferentes volumes.
- **Confidence:** HIGH

### F-010 — [MEDIUM] Erros de callback e tipos inválidos não são traduzidos

- **Catalog rule:** AP-10
- **Location:** `src/AppManager.js:35,46,57-61,92-123,133-136`
- **Evidence:** callbacks ignoram `err`; auditoria falha e ainda pode retornar sucesso; `card` truthy não textual pode causar exceção em `startsWith`; deleção sempre responde sucesso.
- **Impact:** requests podem terminar em falso sucesso, travar ou gerar exceções sem resposta controlada.
- **Recommendation:** validação de entrada, erros tipados e middleware central de tradução.
- **Transformation:** T08/T10
- **Validation:** payloads inválidos e falhas SQLite devem produzir respostas determinísticas sem crash.
- **Confidence:** HIGH

### F-011 — [MEDIUM] Driver SQLite direto está deprecated e sem manutenção

- **Catalog rule:** AP-11
- **Location:** `package.json:9-12`; `package-lock.json:2021-2037`; `src/AppManager.js:1,7`
- **Evidence:** `sqlite3@5.1.7` está resolvido e usado diretamente; o projeto oficial agora marca o pacote como deprecated e não mantido.
- **Impact:** incompatibilidades futuras de Node, dependências de build abandonadas e ausência de correções.
- **Recommendation:** após confirmar o runtime, migrar para `node:sqlite` ou outro driver mantido atrás de um repository/adapter.
- **Transformation:** T11
- **Validation:** restore/load em runtime suportado, testes de persistência e todos os contratos HTTP.
- **Confidence:** HIGH

### F-012 — [LOW] Código morto e nomes opacos prejudicam manutenção

- **Catalog rule:** AP-14
- **Location:** `src/AppManager.js:2,29-33`; `src/utils.js:10,25`
- **Evidence:** `totalRevenue` é importado/exportado sem uso e dados centrais usam nomes como `u`, `e`, `p`, `cid` e `cc`.
- **Impact:** dependências aparentes falsas e revisão mais lenta em fluxo sensível.
- **Recommendation:** remover símbolos mortos e usar nomes orientados ao domínio durante a extração.
- **Transformation:** T08
- **Validation:** busca estática/lint e testes dos fluxos renomeados.
- **Confidence:** HIGH

## Cobertura do catálogo

- **AP-01:** não encontrado; SQL controlado por entrada usa placeholders.
- **AP-02:** F-001 e F-002.
- **AP-03:** F-003 e F-004.
- **AP-04/AP-05:** deduplicados em F-007.
- **AP-06:** F-008.
- **AP-07:** F-005 e F-006.
- **AP-08:** F-009.
- **AP-09:** nenhuma regra/serialização duplicada independente foi comprovada.
- **AP-10:** F-010.
- **AP-11:** F-011.
- **AP-12:** não aplicável; pagamento é simulação local e SMTP não é usado.
- **AP-13:** agregado a F-002; valores de política serão encapsulados junto de F-007.
- **AP-14:** F-012.

## Proposed Refactoring Plan

| Ordem | Findings | Transformação | Arquivos/papéis afetados | Risco | Validação |
|---:|---|---|---|---|---|
| 1 | Todos | Congelar baseline e criar testes de contrato | `tests/**`, bootstrap testável | comportamento atual incerto | 3 endpoints, erros e efeitos persistentes |
| 2 | F-001, F-002 | Configuração validada e logging redigido | `src/config/**`, logger, payment adapter | credenciais ausentes | testes de configuração/log |
| 3 | F-011 | Abstrair e substituir o driver deprecated | `package*.json`, database adapter | runtime Node desconhecido | restore/load e testes SQL |
| 4 | F-005, F-006 | Repositories, FKs e transações | schema/database/repositories | mudança no efeito do DELETE | fault injection e integridade |
| 5 | F-004, F-007, F-008 | Models, casos de uso e dependências injetadas | domain/application/infrastructure | regressão no fluxo assíncrono | testes unitários por caso de uso |
| 6 | F-003, F-010 | Controllers finos, validação, auth e error handler | adapters HTTP, middleware | mudança de autenticação/status | testes autorizados/anônimos e erros |
| 7 | F-009 | Consulta financeira em lote | report repository/presenter | ordem/formato da resposta | query count e comparação de payload |
| 8 | F-012 | Limpeza e nomes de domínio | módulos extraídos | baixo | análise estática e suíte completa |
| 9 | Todos | Boot/readiness, contratos e auditoria final | `src/app.js`, docs, `api.http` | recursos/porta | boot isolado e smoke tests |

Arquivos existentes potencialmente afetados:

- `src/app.js`, `src/AppManager.js`, `src/utils.js`;
- `package.json`, `package-lock.json`;
- `api.http`, `README.md`.

Novos módulos esperados incluem configuração, domínio, casos de uso, adapters HTTP, repositories, infraestrutura, tratamento de erro e testes.

## Expected MVC Target

```text
src/
├── app.js                         # composition root/bootstrap
├── config/
│   └── index.js                   # configuração validada
├── domain/                        # Model
│   ├── user.js
│   ├── course.js
│   ├── enrollment.js
│   └── payment.js
├── application/                   # Controllers/use cases
│   ├── checkout.js
│   ├── financial-report.js
│   └── delete-user.js
├── adapters/http/                 # View/adapter externo
│   ├── routes.js
│   ├── presenters.js
│   ├── validation.js
│   ├── authentication.js
│   └── error-handler.js
└── infrastructure/
    ├── database/
    │   ├── connection.js
    │   └── repositories/
    ├── security/password-hasher.js
    ├── payment/payment-gateway.js
    ├── cache/memory-cache.js
    └── logging/logger.js

tests/
├── unit/
├── integration/
└── contract/
```

Direção pretendida:

```text
HTTP/View → Controller/use case → Domain/ports ← Infrastructure adapters
                                      ↑
                           composition root injeta tudo
```

Para esta API, “View” significa tradução HTTP/JSON; “Controller” orquestra casos de uso; “Model” contém estado, invariantes e interfaces de persistência. Express e SQLite não devem entrar no domínio.

## Risks and Preconditions

- Não há testes automatizados nem baseline de boot validado.
- A versão efetiva do Node.js é desconhecida; a migração para `node:sqlite` depende de runtime compatível.
- A autenticação sugerida altera o contrato público. Um `y` autoriza o plano, mas a política exata deverá ser congelada antes da implementação.
- A correção do `DELETE` altera seu efeito persistente e provavelmente seu texto de resposta.
- O checkout não usa gateway real; a validação deverá empregar test double, sem serviço ou cartão reais.
- O SQLite é efêmero, mas todas as validações usarão instâncias temporárias e isoladas.
- A árvore `node_modules` preexistente será preservada e não será tratada como código first-party.
- O relatório foi persistido antes do checkpoint humano.

## Human Gate

Phase 2 foi concluída com a codebase em modo somente-leitura e este relatório foi salvo em `reports/audit-project-2.md` antes do checkpoint. A Fase 3 foi autorizada e executada em um turno posterior.

**Checkpoint apresentado:** `Phase 2 complete. Autoriza executar a Fase 3 e modificar os arquivos conforme o plano apresentado? [y/n]`

**Checkpoint status:** `APPROVED`

## Phase 3 Results

**Status:** `COMPLETE`

### Changes

- **Report saved at:** `reports/audit-project-2.md`
- **Changed files:** `.env.example`, `.gitignore`, `README.md`, `api.http`, `package*.json`, `src/**` e `tests/**`; `src/AppManager.js` e `src/utils.js` removidos após equivalência.
- **New architecture:** adapters HTTP, application use cases, domínio, configuração e infraestrutura separados; `src/app.js` é o composition root.
- **Resolved findings:** F-001 a F-012.
- **Residual findings/risks:** nenhum finding aberto; chaves continuam sendo credenciais operacionais que devem ser gerenciadas e rotacionadas fora do código.

### Validation Evidence

| Check | Command/method | Result | Evidence |
|---|---|---|---|
| Restore/build/load | load com Node.js v24.15.0 e `node:sqlite` | PASS | `load-ok`; runtime satisfaz `engines >=22.5.0` |
| Static analysis/types/lint | `node --check` em `src/` e `tests/` | PASS | todos os arquivos válidos; não há script de lint dedicado |
| Automated tests | `node --test "tests/**/*.test.js"` | PASS | 16/16 testes |
| Unit boot/readiness | boot em porta temporária e shutdown | PASS | `boot-close-ok` |
| Public contracts | smoke HTTP real | PASS | checkout `200`, impersonação `403`, relatório `200`, DELETE protegido `409` |
| Regression audit | varredura dirigida F-001–F-012 | PASS | identidade vinculada ao e-mail, driver deprecated removido e nenhum finding aberto |
| Scope/diff | `git diff --check -- ecommerce-api-legacy` | PASS | sem erros de whitespace ou escrita fora do projeto |

### Contract Comparison

| Type | Identity | Before | After | Result |
|---|---|---|---|---|
| HTTP | `POST /api/checkout` | sem auth; `200/4xx` | mesmo método/path/shape quando autorizado; `401/403` protegem identidade | PASS — segurança aprovada |
| HTTP | `GET /api/admin/financial-report` | sem auth; `200` array | mesmo payload com papel `admin` | PASS — segurança aprovada |
| HTTP | `DELETE /api/users/:id` | falso sucesso e órfãos | `404/409`, autorização admin e integridade RESTRICT | PASS — correção aprovada |

### Final Status

`COMPLETE`
