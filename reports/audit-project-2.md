================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js, CommonJS) + Express (4.22.1)
Files:   3 analisados | ~180 linhas de código
Database: SQLite em memória (`sqlite3` 5.1.7) / SQL cru via driver, queries parametrizadas

## Summary
| Severidade | Qtde |
|---|---|
| CRITICAL | 2 |
| HIGH     | 4 |
| MEDIUM   | 3 |
| LOW      | 2 |
| **Total** | **11** |

## Current Architecture
Monolítico. `src/AppManager.js` (141 linhas) concentra conexão com o banco, criação de schema e seed, definição de rotas, validação, regra de negócio (pagamento, matrícula, relatório) e SQL. `src/utils.js` mistura config com segredos, cache global e uma função de "criptografia". `src/app.js` é um entry point enxuto, mas apenas instancia o `AppManager`. Não há camadas separadas de routes/controllers/models.

## Findings
(ordenados por severidade: CRITICAL → HIGH → MEDIUM → LOW)

### [CRITICAL] AP-02 — Credenciais e segredos hardcoded
- **File**: `src/utils.js:1-7`
- **Description**: `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (chave live) e `smtpUser` estão literais no código versionado. A porta também é fixa (`port: 3000`).
- **Impact**: qualquer pessoa com acesso ao repositório obtém credenciais de produção e a chave do gateway de pagamento.
- **Recommendation**: mover para variáveis de ambiente lidas em um único módulo `config/` (com `.env.example` sem valores reais) e rotacionar as chaves expostas (Playbook P2).

### [CRITICAL] AP-03 — Exposição de dados sensíveis / autenticação fraca
- **File**: `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:45`, `src/AppManager.js:68`, `src/AppManager.js:80-129`, `src/AppManager.js:131-137`
- **Description**:
  - `badCrypto` não é hash: concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres. Só os 2 primeiros caracteres da senha influenciam o resultado, sem salt (`utils.js:17-23`).
  - Senha padrão `"123456"` para usuários criados sem `pwd` (`AppManager.js:68`); seed com senha em texto puro `'123'` (`AppManager.js:18`).
  - Número completo do cartão e a chave do gateway são impressos no log: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (`AppManager.js:45`).
  - `GET /api/admin/financial-report` e `DELETE /api/users/:id` não têm autenticação nem autorização (`AppManager.js:80`, `131`).
- **Impact**: senhas recuperáveis por força bruta trivial; dados de cartão (PCI) e segredos vazam em logs; qualquer cliente anônimo lê o faturamento ou apaga usuários.
- **Recommendation**: usar hash adequado (bcrypt/scrypt via `crypto.scrypt`) com salt; exigir senha no cadastro (ou rejeitar); nunca logar PAN/chave (no máximo os 4 últimos dígitos); proteger rotas administrativas com um middleware de autenticação (ex.: token admin vindo da config) (Playbook P2, P8).

### [HIGH] AP-04 — God Class / God File
- **File**: `src/AppManager.js:4-139`
- **Description**: a classe `AppManager` acumula 5 responsabilidades: conexão com o banco (`:7`), schema/seed (`:10-23`), roteamento (`:25-137`), regra de negócio de checkout/pagamento (`:43-64`) e geração do relatório financeiro (`:80-129`).
- **Impact**: impossível testar ou evoluir qualquer parte isoladamente.
- **Recommendation**: separar em `database/`, `models/`, `controllers/`, `routes/` e `services/` (Playbook P3, P4).

### [HIGH] AP-05 — Lógica de negócio e acesso a dados nas rotas
- **File**: `src/AppManager.js:28-78`, `src/AppManager.js:80-129`, `src/AppManager.js:131-137`
- **Description**: os handlers executam SQL direto, decidem aprovação do pagamento (`cc.startsWith("4")`, `:46`), criam usuário, matrícula, pagamento e auditoria, e montam o JSON de resposta no mesmo bloco. O `DELETE` apenas remove o usuário e deixa matrículas e pagamentos órfãos (a própria resposta admite: "ficaram sujos no banco", `:135`).
- **Impact**: viola MVC, regra não reutilizável e integridade referencial quebrada.
- **Recommendation**: controllers só orquestram; mover SQL para models e a regra de checkout/relatório para services; ao remover usuário, tratar matrículas/pagamentos relacionados de forma consistente (Playbook P3, P4, P5).

### [HIGH] AP-06 — Estado global mutável e conexão global
- **File**: `src/utils.js:9-15`, `src/utils.js:25`, `src/AppManager.js:7`, `src/AppManager.js:59`
- **Description**: `globalCache` é um objeto mutável de módulo escrito por `logAndCache` a cada checkout e nunca lido ou limpo (cresce sem limite). `totalRevenue` é uma global exportada e não usada. A conexão SQLite é criada dentro do construtor do `AppManager`, acoplando ciclo de vida do banco ao gerenciador de rotas.
- **Impact**: vazamento de memória, estado compartilhado entre requests e testes frágeis.
- **Recommendation**: remover o cache global (ou isolá-lo em um módulo com ciclo de vida e limite); criar a conexão em `database/` e injetá-la nos models (Playbook P6).

### [HIGH] AP-07 — Tratamento de erros ausente ou inadequado
- **File**: `src/AppManager.js:57-61`, `src/AppManager.js:92-94`, `src/AppManager.js:104`, `src/AppManager.js:106`, `src/AppManager.js:133-135`, `src/AppManager.js:35-76`
- **Description**:
  - O erro do insert de `audit_logs` é ignorado e a resposta é sempre sucesso (`:57-60`).
  - Em `:92`, `:104`, `:106` o `err` não é verificado: se `enrollments` vier `undefined`, `enrollments.length` lança `TypeError` dentro de callback assíncrono e derruba o processo.
  - O `DELETE` ignora `err` e sempre responde sucesso (`:133-135`).
  - O checkout não é atômico: usuário, matrícula e pagamento são inseridos em passos separados, sem transação; uma falha no meio deixa dados parciais (`:50-57`, `:69`).
  - Erros são strings soltas ("Erro DB", "Erro Matrícula"...), sem formato uniforme nem handler central.
- **Impact**: falhas silenciosas, crash do servidor e dados inconsistentes.
- **Recommendation**: tratador central de erros com formato `{ "error": "..." }`, verificação de `err` em todo I/O, transação no checkout (Playbook P7).

### [MEDIUM] AP-08 — Problema N+1 / queries ineficientes
- **File**: `src/AppManager.js:83-127`
- **Description**: o relatório financeiro faz 1 query de cursos e, para cada curso, 1 de matrículas, e para cada matrícula mais 2 (usuário e pagamento). Usa `SELECT *` (`:83`, `:92`). Sem paginação.
- **Impact**: latência cresce com o produto cursos × matrículas; a ordem do array `report` depende da ordem de término dos callbacks (não determinística).
- **Recommendation**: substituir por uma única query com `JOIN` (cursos, matrículas, usuários, pagamentos) e agrupar em memória (Playbook P9).

### [MEDIUM] AP-09 — Validação de entrada ausente ou inadequada
- **File**: `src/AppManager.js:29-35`, `src/AppManager.js:131-133`
- **Description**: o checkout só verifica presença de `usr`, `eml`, `c_id`, `card`. Não valida formato de e-mail, tipo de `c_id` nem formato do cartão; `pwd` é opcional com fallback silencioso (`:68`). `req.params.id` do `DELETE` não é validado.
- **Impact**: dados inválidos gravados, comportamento imprevisível.
- **Recommendation**: validar no controller/middleware (tipos, e-mail, comprimento do cartão, id numérico) e responder 400 padronizado (Playbook P5).

### [MEDIUM] AP-13 — API deprecated / padrões obsoletos
- **File**: `src/AppManager.js:37-77`, `src/AppManager.js:83-127`
- **Description**: callbacks aninhados em até 7 níveis (callback hell) com `sqlite3`, em vez de `async/await`/Promises. Nenhuma API removida do Express 4.22.1 foi detectada.
- **Impact**: código difícil de ler e de tratar erros corretamente (origem de AP-07).
- **Recommendation**: encapsular o driver em Promises (`util.promisify` ou wrappers `run/get/all`) e usar `async/await` (Playbook P11).

### [LOW] AP-11 — Magic numbers e strings
- **File**: `src/AppManager.js:21`, `src/AppManager.js:46`, `src/AppManager.js:48`, `src/AppManager.js:68`, `src/AppManager.js:108`, `src/utils.js:19-22`
- **Description**: status `"PAID"`/`"DENIED"` repetidos; regra de aprovação `cc.startsWith("4")`; senha padrão `"123456"`; `10000`, `0, 2` e `0, 10` em `badCrypto`.
- **Impact**: significado implícito, alteração propensa a erro.
- **Recommendation**: extrair constantes nomeadas (`PAYMENT_STATUS`, etc.) (Playbook P10).

### [LOW] AP-12 — Nomenclatura e convenções inconsistentes
- **File**: `src/AppManager.js:2`, `src/AppManager.js:26`, `src/AppManager.js:29-33`, `src/AppManager.js:45`, `src/utils.js:13`, `src/app.js:13`
- **Description**: variáveis de uma letra (`u`, `e`, `p`, `cid`, `cc`, `enr`); alias `self`; imports não usados (`totalRevenue`, `badCrypto` aproveitado só pela rota); `let` onde cabe `const`; mensagens misturando PT/EN; `console.log` de debug em vez de logger; nome "Frankenstein LMS" no log de boot.
- **Impact**: legibilidade reduzida.
- **Recommendation**: nomes descritivos, `const`, remoção de imports mortos, logger único (Playbook P10).

## Deprecated APIs
| API obsoleta | Local | Equivalente moderno | Severidade |
|---|---|---|---|
| Callbacks aninhados (sqlite3) | `src/AppManager.js:37-77`, `:83-127` | `async/await` com wrappers Promise | MEDIUM |
| Hash caseiro `badCrypto` (equivalente a hash fraco) | `src/utils.js:17-23` | bcrypt/argon2/scrypt | CRITICAL (ver AP-03) |

## Target Architecture (proposta)
```
ecommerce-api-legacy/
├── src/
│   ├── app.js                      # composition root (cria app, registra rotas, listen)
│   ├── config/
│   │   └── index.js                # lê env vars (porta, chaves, token admin)
│   ├── database/
│   │   ├── connection.js           # conexão SQLite + helpers Promise (run/get/all)
│   │   └── schema.js               # DDL + seed
│   ├── models/
│   │   ├── userModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   ├── paymentModel.js
│   │   └── auditLogModel.js
│   ├── services/
│   │   ├── checkoutService.js      # regra de checkout/pagamento (transação)
│   │   ├── paymentGateway.js       # decisão do pagamento + log seguro
│   │   └── reportService.js        # relatório financeiro (JOIN)
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── reportController.js
│   │   └── userController.js
│   ├── routes/
│   │   └── index.js
│   ├── middlewares/
│   │   ├── adminAuth.js
│   │   └── errorHandler.js
│   └── utils/
│       └── password.js             # hash/verify (scrypt)
├── package.json
└── api.http
```

================================
Total: 11 achados (2 critical, 4 high, 3 medium, 2 low)
================================

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]
