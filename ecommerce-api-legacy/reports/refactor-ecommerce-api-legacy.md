# Refactor Report — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 3 — Refatoração).
> Data: 2026-10-22 | Atualizado: 2026-10-31 (reauditoria SEC-04 — regra expandida)
> Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
> Baseado em: `reports/analysis-ecommerce-api-legacy.md` e `reports/audit-ecommerce-api-legacy.md`

## 1. Resumo

| Métrica | Antes | Depois |
|---|---|---|
| Arquitetura | Flat / monolito desestruturado | MVC + Services + Repositories |
| Arquivos de código | 3 JS | 36 JS + 1 SQL |
| LOC de código | ~180 | ~867 |
| Testes | 0 | 16 testes (`node:test`) |
| Dependências | `express`, `sqlite3` | `express`, `sqlite3`, `dotenv` |
| Entrypoint | `src/app.js` (rotas + boot) | `src/app.js` (composição + boot) |
| Schema | DDL inline no boot | Migrations SQL versionadas (`schema_migrations`) |
| Config | Literais em `src/utils.js` | `process.env` + `.env` via `dotenv` |
| Auth admin | Inexistente | Bearer token com fail-closed |
| Anti-patterns corrigidos | — | 13/13 (2 CRITICAL, 4 HIGH, 4 MEDIUM, 3 LOW) |
| Endpoints validados | — | 3/3 rotas de contrato + caminhos de erro |
| Reauditoria SEC-04 (2026-10-31) | — | 1 gap adicional (checkout IDOR) corrigido |

**Resultado:** refatoração concluída. A aplicação sobe com `npm start`, os 16 testes passam e o smoke test exercitou todas as rotas inventariadas na Fase 1, incluindo os caminhos de 400, 401, 404 e 503.

### Estrutura antes

```
src/
├── app.js          # bootstrap + Express
├── AppManager.js   # schema + rotas + negócio + SQL
└── utils.js        # config hardcoded + cache global + crypto caseiro
```

### Estrutura depois

```
src/
├── app.js                     # composição da aplicação e boot
├── container.js               # injeção de dependências
├── config/index.js            # configuração via ambiente (.env)
├── database/
│   ├── connection.js          # conexão SQLite + wrapper async + transaction
│   ├── migrator.js            # runner de migrations + schema_migrations
│   ├── schema.js              # seeds idempotentes
│   └── migrations/
│       └── 001_initial_schema.sql
├── models/
│   ├── User.js                # validação/factory de usuário
│   ├── Course.js              # invariante de curso comprável
│   ├── Enrollment.js          # factory de matrícula
│   └── Payment.js             # factory + status de pagamento
├── repositories/
│   ├── UserRepository.js
│   ├── CourseRepository.js
│   ├── EnrollmentRepository.js
│   ├── PaymentRepository.js
│   ├── AuditLogRepository.js
│   └── ReportRepository.js
├── services/
│   ├── CheckoutService.js
│   ├── FinancialReportService.js
│   ├── UserService.js
│   └── PaymentGateway.js
├── controllers/
│   ├── CheckoutController.js
│   ├── FinancialReportController.js
│   └── UserController.js
├── routes/
│   ├── index.js
│   ├── checkoutRoutes.js
│   ├── adminRoutes.js
│   └── userRoutes.js
├── middleware/
│   ├── auth.js
│   ├── asyncHandler.js
│   ├── errorHandler.js
│   └── notFound.js
├── validators/
│   ├── checkoutValidator.js
│   └── idValidator.js
├── utils/
│   ├── logger.js
│   └── password.js
└── errors/index.js
```

## 2. Anti-patterns corrigidos

Todos os 13 achados da auditoria foram corrigidos.

| ID | Severidade | Evidência anterior | Como foi corrigido | Evidência nova |
|---|---|---|---|---|
| SEC-02 | CRITICAL | `src/utils.js:2-5` — usuário/senha de banco, chave live e SMTP literais | Config centralizada em `process.env` com `dotenv`; segredos obrigatórios falham no boot em produção; `.env.example` sem valores reais. Campos legados não usados (`dbUser`, `dbPass`, `smtpUser`) foram removidos. | `src/config/index.js:1-30`; `.env.example` |
| SEC-03 | CRITICAL | `src/utils.js:17-23` — base64 repetido/truncado, sem salt; senha seed `'123'` | `scrypt` com salt aleatório de 16 bytes, chave de 64 bytes e `timingSafeEqual`; seed usa senha aleatória gravada apenas como hash. | `src/utils/password.js:1-31`; `src/database/schema.js:9-15`; `tests/password.test.js` |
| SEC-04 | HIGH | `src/AppManager.js:80,131` — relatório admin e DELETE abertos; `src/AppManager.js:28-77` — checkout aceita e-mail de conta existente sem provar posse (IDOR) | Middleware `requireAdmin` com Bearer token em tempo constante nas rotas administrativa/destrutiva (sem `ADMIN_TOKEN` → 503 fail-closed). No checkout, novo usuário continua público; para conta existente o service exige `pwd` válido (`verifyPassword`) e responde 401 sem senha ou com senha incorreta. O dono é derivado da conta autenticada, nunca de id/role do body. | `src/middleware/auth.js:1-27`; `src/routes/adminRoutes.js:5`; `src/routes/userRoutes.js:5`; `src/services/CheckoutService.js:38-48`; `src/errors/index.js:17-21` |
| SEC-06 | HIGH | `src/AppManager.js:45` — cartão completo + chave do gateway no log | Log estruturado apenas com `cardLast4`, `userId`, `courseId` e status; a chave nunca é logada. | `src/services/CheckoutService.js:51-57` |
| ARCH-01 | HIGH | `src/AppManager.js:29-75,81-129` — pagamento, criação de usuário e agregação dentro dos handlers | Regras extraídas para `CheckoutService`, `FinancialReportService` e `UserService`; controllers só validam/orquestram/serializam. | `src/services/CheckoutService.js:34-82`; `src/services/FinancialReportService.js:8-31`; `src/controllers/*.js` |
| ARCH-02 | HIGH | `src/AppManager.js:37,40,50,54,57,69,83,92,104,106,133` — SQL nos handlers | Seis repositories por agregado; queries parametrizadas com `?`; services não escrevem SQL. | `src/repositories/*.js` |
| PERF-01 | MEDIUM | `src/AppManager.js:89-127` — `1 + C + 2E` queries em loops | Uma query com `LEFT JOIN` de cursos → matrículas → usuários → pagamentos; agregação em memória preservando ordem e formato. | `src/repositories/ReportRepository.js:7-24`; `src/services/FinancialReportService.js:8-31` |
| QUAL-02 | MEDIUM | `src/AppManager.js:29-35,132` — validação só de presença | Validadores de checkout (tipos, e-mail, cartão 13–19 dígitos, `c_id` inteiro positivo) e de `:id`; erros → 400. | `src/validators/checkoutValidator.js`; `src/validators/idValidator.js` |
| QUAL-03 | MEDIUM | `src/AppManager.js:57,83,92,104,106,133-136` — `err` ignorado e DELETE sempre 200 | `async/await` + `asyncHandler`; error handler central de 4 parâmetros; transações com rollback; erros de domínio mapeados para 400/404; 500 genérico sem vazar detalhes. | `src/middleware/errorHandler.js`; `src/middleware/asyncHandler.js`; `src/database/connection.js:30-46` |
| QUAL-04 | MEDIUM | `src/utils.js:9-15,25` — `globalCache` e `totalRevenue` globais | Estado global removido; dependências injetadas via `container.js`; cache inexistente no fluxo atual e `totalRevenue` morto eliminado. | `src/container.js`; `src/utils/logger.js` |
| QUAL-06 | LOW | `src/AppManager.js:10-23` — DDL inline no boot, sem migrations | Migrations SQL em `src/database/migrations/`, runner com tabela `schema_migrations`, aplicação transacional e idempotente. | `src/database/migrator.js`; `src/database/migrations/001_initial_schema.sql` |
| QUAL-07 | LOW | `src/utils.js:1-7` — porta e config literais | Porta, caminho do banco, token e chave lidos de ambiente, com validação e defaults apenas para valores não-sensíveis. | `src/config/index.js`; `.env.example` |
| QUAL-08 | LOW | `package.json:6-8` — nenhum teste | Suíte com `node:test` (sem dependência extra) cobrindo as três rotas, autenticação, validação, agregação, cascade delete e hash. | `tests/api.test.js`; `tests/password.test.js`; `package.json:6-9` |

### Correções estruturais adicionais

- **Transações:** checkout grava matrícula, pagamento e auditoria em uma transação (`src/services/CheckoutService.js:61-81`); DELETE remove pagamentos, matrículas e usuário na mesma transação (`src/services/UserService.js:14-24`).
- **Integridade referencial:** migrations declaram FKs com `ON DELETE CASCADE` e índices para FKs (`src/database/migrations/001_initial_schema.sql`).
- **Erros de domínio:** `ValidationError`, `NotFoundError`, `PaymentDeniedError` (`src/errors/index.js`).
- **Config fail-fast:** em `NODE_ENV=production`, ausência de `ADMIN_TOKEN` ou `PAYMENT_GATEWAY_KEY` aborta o boot (`src/config/index.js:3-8`).
- **Cleanup:** `src/AppManager.js` e `src/utils.js` foram removidos; nenhum import ou referência legada permanece.
- **Dotenv:** adicionado `dotenv@18.0.9` para carregar `.env`, com variáveis de ambiente tendo precedência.

## 3. Validação

### 3.1 Boot e testes automatizados

- **Comando de boot da Fase 1:** `npm start` → `node src/app.js`.
- **Resultado:** aplicação sobe e registra `Frankenstein LMS rodando na porta 3004...` em JSON (`src/app.js:23-25`).
- **Suíte:** `npm test` → **16/16 testes passando** (0 falhas).
- **Migrations idempotentes:** executar `initializeSchema` duas vezes resultou em `schema_migrations = ["001_initial_schema.sql"]` e `users = 1`, sem duplicar seeds.
- **Fail-fast de produção:** `NODE_ENV=production` sem segredos aborta o boot; com `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` definidos, carrega normalmente.

### 3.2 Endpoints — contrato e caminhos de erro

| # | Rota / cenário | Resultado observado | Status |
|---|---|---|---|
| 1 | `POST /api/checkout` — sucesso (cartão `4...`, curso 2) | `200 {"msg":"Sucesso","enrollment_id":2}` | ✅ |
| 2 | `POST /api/checkout` — pagamento recusado (cartão `5...`) | `400 Pagamento recusado` | ✅ |
| 3 | `POST /api/checkout` — payload malformado | `400 Bad Request` | ✅ |
| 4 | `POST /api/checkout` — curso inexistente (`c_id: 999`) | `404 Curso não encontrado` | ✅ |
| 5 | `POST /api/checkout` — novo usuário sem `pwd` | `400 pwd é obrigatório para novo usuário` | ✅ (mudança documentada) |
| 5a | `POST /api/checkout` — usuário existente sem `pwd` | `401 Credenciais inválidas` | ✅ (SEC-04, novo) |
| 5b | `POST /api/checkout` — usuário existente com `pwd` incorreta | `401 Credenciais inválidas` | ✅ (SEC-04, novo) |
| 5c | `POST /api/checkout` — usuário existente com `pwd` correta | `200 {"msg":"Sucesso","enrollment_id":N}` | ✅ (SEC-04, novo) |
| 6 | `GET /api/admin/financial-report` — com token | `200` array `[{course, revenue, students:[{student, paid}]}]` | ✅ |
| 7 | `GET /api/admin/financial-report` — sem token | `401 {"error":"Unauthorized"}` | ✅ (novo) |
| 8 | `GET /api/admin/financial-report` — sem `ADMIN_TOKEN` configurado | `503 {"error":"Admin authentication is not configured"}` | ✅ (novo) |
| 9 | `DELETE /api/users/:id` — com token | `200 Usuário deletado com sucesso.` | ✅ (mensagem alterada) |
| 10 | `DELETE /api/users/:id` — sem token | `401` | ✅ (novo) |
| 11 | `DELETE /api/users/:id` — usuário inexistente | `404 Usuário não encontrado` | ✅ (novo) |
| 12 | `DELETE /api/users/:id` — id inválido (`abc`) | `400 Bad Request` | ✅ (novo) |
| 13 | Rota inexistente (`GET /api/nope`) | `404 {"error":"Not found"}` | ✅ (novo) |
| 14 | Relatório após checkout aprovado | Curso `Docker` com `revenue: 497` e estudante `Guilherme` | ✅ |
| 15 | Relatório após DELETE do usuário 1 | Curso `Clean Architecture` com `revenue: 0` e `students: []` (sem órfãos) | ✅ |

### 3.3 Checklist da Fase 3 (`mvc-guidelines.md` §6)

- [x] Aplicação sobe sem erros com o comando de boot (`npm start`).
- [x] Todas as rotas inventariadas respondem no mesmo path/verbo; formatos de sucesso preservados.
- [x] Rotas de escrita rejeitam payload malformado/ausente com 400.
- [x] Nenhuma query interpolada — todas usam `?` com bindings; a única query com template literal é SQL estático sem interpolação (`ReportRepository.js:7-24`).
- [x] Nenhum segredo literal no código — grep por padrões legados/SEC-02 retornou vazio.
- [x] Responses não expõem senha/hash; `findByEmail` usa `pass` apenas internamente e nenhum controller serializa usuário.
- [x] Nenhum bloco de captura genérica engolindo erro sem log; rollback preserva o erro original em `err.rollbackError`.
- [x] Arquivos antigos removidos (`src/AppManager.js`, `src/utils.js`); nenhum import morto detectado.
- [x] `git status` contém apenas mudanças esperadas da refatoração (além de arquivos preexistentes fora do projeto).
- [x] Checks estáticos: todos os arquivos passam em `node --check`; todos os módulos carregam via `require`.

## 4. Mudanças de contrato (documentadas)

A refatoração preservou os contratos principais, mas a auditoria exigiu mudanças pontuais:

1. **Rotas administrativas agora exigem autenticação** (`GET /api/admin/financial-report` e `DELETE /api/users/:id`). Sem token → `401`; sem `ADMIN_TOKEN` configurado → `503`. Clientes anônimos precisam ser ajustados.
2. **DELETE agora é transacional e remove dependências** (pagamentos e matrículas). A mensagem de sucesso mudou de `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` para `"Usuário deletado com sucesso."`.
3. **Novo usuário sem `pwd`** agora recebe `400 pwd é obrigatório para novo usuário`; antes havia fallback silencioso para `"123456"`. **Usuário existente agora precisa informar a senha correta**: sem `pwd` ou com senha incorreta → `401 Credenciais inválidas` (SEC-04/IDOR). O usuário novo só é persistido após a aprovação do pagamento, na mesma transação de matrícula/pagamento/auditoria.
4. **Validação mais estrita:** e-mail inválido, cartão fora de 13–19 dígitos ou `:id` não numérico retornam `400` (antes eram aceitos ou causavam comportamento indefinido).
5. **Erros internos** retornam `500 Internal Server Error` genérico, em vez de mensagens específicas de banco (`"Erro DB"`, `"Erro Matrícula"`, etc.).
6. **404 de rota inexistente** agora é JSON (`{"error":"Not found"}`) em vez do HTML padrão do Express.
7. **Seed:** o usuário `Leonan` recebe senha aleatória armazenada como hash; não há fluxo de login neste serviço, então o valor não é utilizável externamente.
8. **Schema:** `users.email` agora é `UNIQUE`/`NOT NULL`; FKs e índices foram adicionados.

Contratos preservados: `POST /api/checkout` mantém `200 {"msg":"Sucesso","enrollment_id":N}`; o relatório mantém o array `[{course, revenue, students:[{student, paid}]}]` e a semântica de receita (apenas `PAID` soma, `paid` reflete o valor do pagamento); a regra de aprovação por cartão iniciado em `4` foi mantida.

## 5. Limitações e trabalho futuro

- **Autenticação:** o token admin é estático e único, sem usuários, roles, expiração ou revogação. Para produção, integrar provedor de identidade (JWT/OIDC) e RBAC; rotacionar o token periodicamente. O checkout de conta existente usa a senha do titular como prova de posse, mas não há verificação de e-mail no cadastro público — um terceiro ainda pode pré-registrar um e-mail conhecido (account pre-hijacking); exigir confirmação de e-mail em produção.
- **Pagamento:** o gateway continua simulado por prefixo do cartão. Integrar o provedor real usando `PAYMENT_GATEWAY_KEY`, com tokenização de cartão e conformidade PCI; nunca logar PAN.
- **Persistência:** o default é SQLite em memória. Usar `DATABASE_PATH` para arquivo/volume persistente; migrations já estão prontas, mas faltam backup, restore e estratégia de rollback operacional.
- **Operação:** não há rate limiting, CORS, `helmet`, timeout de request, correlation ID, métricas ou tracing; o logger é JSON básico.
- **Testes:** a suíte cobre os caminhos principais, mas não carga/concorrência, falhas de banco ou cobertura mínima. Adicionar testes unitários de services/repositories e threshold de cobertura.
- **Delete:** é hard delete. Avaliar soft delete e retenção de auditoria conforme requisitos legais (LGPD).
- **CI/CD e containerização:** continuam ausentes; adicionar pipeline com `npm ci`, `npm test`, lint e build de imagem.
- **Clientes HTTP:** `api.http` usa `{{$processEnv ADMIN_TOKEN}}`; alguns clientes REST podem não suportar essa sintaxe e precisam de ajuste local.
- **SMTP/e-mail:** a configuração legada de SMTP foi removida por não ter uso; se notificações forem necessárias, criar integração dedicada.

## 6. Adendo — reauditoria SEC-04 (2026-10-31)

A regra SEC-04 foi ampliada para cobrir rotas de cadastro/criação que aceitam identidade ou dono vindos do cliente. Reauditando o estado refatorado:

- `GET /api/admin/financial-report` e `DELETE /api/users/:id`: já protegidos por `requireAdmin` (`401` sem token; `503` sem `ADMIN_TOKEN`).
- `POST /api/checkout`: gap residual. O service buscava o usuário por `email` e criava matrícula/pagamento em nome dele sem verificar `pwd`. Um cliente anônimo podia comprar em nome de terceiro (IDOR) conhecendo apenas o e-mail.

**Correção aplicada:**

- `CheckoutService` passou a validar `verifyPassword(password, existingUser.pass)` quando o e-mail já existe; sem senha ou senha incorreta → `UnauthorizedError` (`401 Credenciais inválidas`).
- A criação do usuário novo foi movida para dentro da transação, depois da aprovação do pagamento.
- Nenhum campo de posse/privilégio (`user_id`, `owner_id`, `role`, `tipo`) é lido do body; o dono é a conta autenticada por e-mail + senha.
- Testes adicionados: novo usuário sem `pwd` (`400`), existente sem `pwd` (`401`), existente com `pwd` errada (`401`), existente com `pwd` correta (`200`) — **16/16 passando**.
- Smoke test: `401 Credenciais inválidas` nos dois casos negativos; `200` com a senha correta; admin segue `401` sem token e `200` com token.

**Risco residual:** cadastro público sem verificação de e-mail permite pré-registro de e-mail de terceiros (account pre-hijacking). Não permite assumir uma conta já existente, mas deve ser endereçado com confirmação de e-mail em produção.
