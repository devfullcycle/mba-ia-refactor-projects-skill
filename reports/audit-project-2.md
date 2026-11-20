================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2 (installed 4.22.1) (SQLite in-memory via sqlite3 5.1.7 raw driver)
Files:   3 analyzed | ~180 lines of code
Architecture: Monolithic — `AppManager.js` owns DB init, schema, seeds, all 3 routes, payment and report logic

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] AP-04 Unprotected administrative / destructive endpoints
File: src/AppManager.js:80-129, 131-137
Description: `GET /api/admin/financial-report` (linha 80) devolve nome de cada aluno e valores pagos, e `DELETE /api/users/:id` (linha 131) apaga usuários — ambos sem qualquer middleware de autenticação/autorização (`app.js:6` registra apenas `express.json()`).
Impact: Qualquer chamador anônimo lê dados financeiros/PII de todos os alunos e apaga qualquer usuário.
Recommendation: Middleware de autenticação admin (token via variável de ambiente) aplicado às rotas `/api/admin/*` e `DELETE /api/users/:id`. (T-17)

### [CRITICAL] AP-06 Sensitive data exposure in logs
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave do gateway (`pk_live_****`) no stdout a cada checkout — confirmado no boot de verificação (`Processando cartão 4111 na chave pk_live_****`).
Impact: Violação PCI-DSS/LGPD; qualquer leitor de log obtém PAN de cartões e a chave de produção do gateway.
Recommendation: Nunca logar PAN nem segredos; logar no máximo os 4 últimos dígitos via logger estruturado. (T-10)

### [CRITICAL] AP-01 Hardcoded secrets and credentials
File: src/utils.js:1-7
Description: Objeto `config` com literais: `dbPass: "senha_super_****"` (l.3), `paymentGatewayKey: "pk_live_****"` (l.4), além de `dbUser` (l.2), `smtpUser` (l.5) e `port: 3000` (l.6); nada é lido de `process.env`.
Impact: Credenciais de produção expostas a quem tem acesso ao repositório; impossível rotacionar ou variar por ambiente.
Recommendation: Módulo `config/` lendo `process.env` com defaults seguros apenas para dev e `.env.example` documentando as variáveis. (T-01)

### [CRITICAL] AP-05 Insecure password storage
File: src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18
Description: `badCrypto` concatena 10000× os 2 primeiros caracteres do base64 da senha e trunca em 10 (`substring(0, 10)`) — reversível e colide para senhas com o mesmo prefixo; quando `pwd` não é enviado, usa a senha padrão `"123456"` (l.68). O seed grava `pass` `'123'` em texto puro (l.18).
Impact: Um vazamento do banco expõe as senhas (base64 é reversível); senhas como "abc" e "abcdef" geram o mesmo "hash"; contas criadas sem senha ficam com senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório (stdlib) e comparação em tempo constante; exigir senha no cadastro. (T-09)

### [CRITICAL] AP-03 God Class (no separation of concerns)
File: src/AppManager.js:1-141, src/utils.js:1-25
Description: `AppManager` concentra conexão (l.7), DDL + seeds (l.10-23), registro de rotas HTTP (l.25-137), regra de pagamento (l.46), persistência e auditoria (l.50-63) e agregação de relatório (l.80-129). `utils.js` mistura configuração/segredos, cache e "criptografia".
Impact: Nenhuma parte pode ser testada isoladamente; qualquer mudança afeta todas as features (viola SRP/MVC).
Recommendation: Dividir em config, models (repositórios), controllers, routes, services e composition root. (T-03)

### [HIGH] AP-14 Missing input validation (process crash)
File: src/AppManager.js:35, 46, 68, 132
Description: Só há checagem de presença (`if (!u || !e || !cid || !cc)`, l.35). `card` numérico chega em `cc.startsWith("4")` (l.46) dentro de um callback do sqlite e lança `TypeError: cc.startsWith is not a function` — confirmado: o processo Node encerrou com exit code 1. `c_id`, formato de `eml` e `:id` (l.132) não são validados. Elevado de MEDIUM para HIGH: uma única requisição anônima derruba a API inteira (DoS).
Impact: Qualquer cliente derruba o servidor para todos os usuários com um payload `{"card": 4111}`.
Recommendation: Validação centralizada de tipos/formato antes do controller, respondendo 400. (T-14)

### [HIGH] AP-10 Non-atomic multi-step writes / broken referential integrity
File: src/AppManager.js:50-63, 66-72, 131-137, 12-16
Description: Criação de usuário → `INSERT enrollments` → `INSERT payments` → `INSERT audit_logs` executados em sequência sem `BEGIN/COMMIT/ROLLBACK`; falha intermediária deixa matrícula sem pagamento. `DELETE FROM users` (l.133) não trata `enrollments`/`payments` — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". As tabelas não têm `FOREIGN KEY` (l.12-16).
Impact: Dados órfãos/parciais corrompem o relatório financeiro (aluno "Unknown" com pagamento).
Recommendation: Transação única para o checkout; exclusão de usuário em transação removendo pagamentos e matrículas (ou FKs com cascade). (T-11)

### [HIGH] AP-11 Callback hell / pyramid of doom
File: src/AppManager.js:37-77, 83-128, 57, 92-93, 104, 106, 133
Description: 6 níveis de callbacks aninhados no checkout e contadores manuais `coursesPending--`/`enrPending--` no relatório. Erros ignorados: `(err) => {` sem checagem em l.57, 104, 106, 133; em l.92-93 um erro deixaria `enrollments` indefinido e `enrollments.length` derrubaria o processo. Ordem dos cursos no relatório depende da ordem de conclusão dos callbacks (baseline: "Docker" antes de "Clean Architecture").
Impact: Fluxo ilegível, erros silenciosos, risco de resposta dupla e saída não determinística.
Recommendation: Promisificar o driver e reescrever com `async/await` + `try/catch` centralizado. (T-12)

### [HIGH] AP-07 Business logic in route handlers (Fat route)
File: src/AppManager.js:28-78, 80-129
Description: O handler de checkout (51 linhas) faz parsing, validação, busca de curso, criação de usuário, regra de aprovação de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), matrícula, auditoria e cache. O handler do relatório (50 linhas) faz a agregação de receita (`courseData.revenue += payment.amount`).
Impact: Regras de pagamento e relatório não são reutilizáveis nem testáveis sem HTTP.
Recommendation: Mover orquestração para `CheckoutController`/`ReportController` e manter as rotas finas. (T-04)

### [HIGH] AP-08 Tight coupling / no dependency injection
File: src/AppManager.js:7, src/app.js:8-10
Description: O construtor instancia a própria conexão (`this.db = new sqlite3.Database(':memory:')`); `app.js` cria `new AppManager()` que monta DB, seeds e rotas — não há composition root nem injeção.
Impact: Impossível trocar banco ou gateway em testes; todas as camadas dependem de concretos (viola DIP).
Recommendation: App factory que cria DB → repositórios → services → controllers → rotas e injeta as dependências. (T-05)

### [HIGH] AP-09 Global mutable state
File: src/utils.js:9-15, 25
Description: `let globalCache = {}` (l.9) recebe uma entrada por checkout via `logAndCache` (l.14) e nunca é limpo; `let totalRevenue = 0` (l.10) é estado mutável exportado; ambos são exportados (l.25).
Impact: Crescimento ilimitado de memória e acoplamento oculto entre módulos; estado compartilhado entre requisições.
Recommendation: Remover estado global; se cache for necessário, um service injetado com limite de tamanho. (T-06)

### [MEDIUM] AP-13 N+1 queries
File: src/AppManager.js:89-106
Description: Para cada curso (`courses.forEach`, l.89) uma query de matrículas (l.92), e para cada matrícula (`enrollments.forEach`, l.102) uma query de usuário (l.104) e uma de pagamento (l.106): 1 + C + 2·E queries.
Impact: Tempo de resposta e carga no banco crescem linearmente com o número de matrículas.
Recommendation: Uma única query com `LEFT JOIN` courses/enrollments/users/payments e agregação em memória. (T-08)

### [MEDIUM] AP-16 Inconsistent / absent error handling
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 133-135, src/app.js:5-10
Description: Erros são texto puro com mensagens ad-hoc (`"Bad Request"`, `"Erro DB"`, `"Erro Matrícula"`) enquanto o sucesso é JSON; l.38 trata erro de banco como 404; o DELETE sempre responde sucesso, mesmo com erro ou usuário inexistente; `app.js` não registra middleware de erro `(err, req, res, next)`.
Impact: Clientes não conseguem tratar erros de forma uniforme; falhas reais ficam ocultas.
Recommendation: Classes de erro de domínio + middleware de erro central (mantendo status codes atuais do caminho feliz). (T-07)

### [MEDIUM] AP-18 Side effects and infrastructure in the wrong place
File: src/AppManager.js:10-23, 45-46, src/utils.js:12-15
Description: DDL e seeds misturados à classe que também roteia (l.10-23); o "gateway de pagamento" é simulado inline no handler (l.45-46); "cache" com log em `utils.js` (l.12-15).
Impact: Domínio acoplado à infraestrutura; impossível substituir o gateway por um real/mock.
Recommendation: `database` (schema/seed) separado, `PaymentGateway` como service injetado pelo composition root. (T-05)

### [MEDIUM] AP-17 Deprecated / legacy APIs
File: src/AppManager.js:1, 37-136
Description: Uso exclusivamente por callbacks do driver `sqlite3` (onde a alternativa moderna é `util.promisify`/`async-await`), e `require('sqlite3').verbose()` (l.1) ativo em código de produção. `node --trace-deprecation` não emitiu avisos em Node v22.20.0.
Impact: Mantém o callback hell (AP-11) e adiciona overhead de stack trace em produção.
Recommendation: Wrapper promisificado (`run/get/all` → Promise) e `.verbose()` apenas em desenvolvimento. (T-13)

### [MEDIUM] AP-15 Code duplication
File: src/AppManager.js:95-99, 117-122, 41, 84
Description: O bloco de finalização `report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report);` é repetido em dois pontos; mensagem/tratamento `"Erro DB"` duplicado.
Impact: Correções precisam ser aplicadas em vários lugares; risco de divergência.
Recommendation: Agregação única no controller e tratamento de erro centralizado. (T-15, T-04)

### [LOW] AP-19 Magic numbers and magic strings
File: src/AppManager.js:7, 21, 46, 48, 68, 108, src/utils.js:6, 19
Description: Status `'PAID'`/`'DENIED'` repetidos (l.21, 46, 48, 108), prefixo de aprovação `"4"` (l.46), senha padrão `"123456"` (l.68), `':memory:'` (l.7), porta `3000` (utils l.6), laço `10000` (utils l.19).
Impact: Significado oculto; alterar uma regra exige caçar literais.
Recommendation: Constantes nomeadas (`PaymentStatus`) e valores em config. (T-15)

### [LOW] AP-20 Poor naming
File: src/AppManager.js:4, 29-33, 89, 102, src/utils.js:1, 17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc` (l.29-33), `c`, `enr`; classe `AppManager`; função `badCrypto`; `utils.js` guardando configuração. Campos públicos `usr`/`eml`/`pwd`/`c_id`/`card` são crípticos (manter por compatibilidade).
Impact: Legibilidade ruim; nomes não revelam intenção.
Recommendation: Renomear internamente mantendo os nomes de campos da API. (T-16)

### [LOW] AP-21 Unused imports, variables and dead code
File: src/AppManager.js:2, src/utils.js:2-3, 5, 10, 25
Description: `totalRevenue` importado (l.2) e nunca usado; `config.dbUser`, `config.dbPass`, `config.smtpUser` nunca lidos (SQLite em memória não usa credenciais; não há SMTP); `globalCache` exportado e não consumido.
Impact: Ruído e dependências enganosas (sugerem infraestrutura que não existe).
Recommendation: Remover código e configuração mortos. (T-16)

### [LOW] AP-22 console.log as logging
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Description: `console.log` usado para mensagens operacionais no caminho da requisição e no boot, sem níveis.
Impact: Sem níveis/estrutura; não pode ser silenciado (e vazou dados — ver AP-06).
Recommendation: Logger mínimo com níveis (`info`/`error`) controlado por `LOG_LEVEL`. (T-16)

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| src/AppManager.js:37-136 | callback-only `sqlite3` usage (`db.get/all/run(..., cb)`) | `util.promisify` wrapper + `async`/`await` |
| src/AppManager.js:1 | `require('sqlite3').verbose()` in production path | enable only when `NODE_ENV=development` |

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| POST | /api/checkout | src/AppManager.js:28 |
| GET | /api/admin/financial-report | src/AppManager.js:80 |
| DELETE | /api/users/:id | src/AppManager.js:131 |

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
