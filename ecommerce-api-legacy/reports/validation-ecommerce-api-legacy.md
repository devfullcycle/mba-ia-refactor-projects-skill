# Validation Report — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 4 — Validação Pós-Refatoração).
> Data: 2026-10-22 | Atualizado: 2026-10-31 (revalidação SEC-04 — regra expandida)
> Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
> Baseado em: `reports/analysis-ecommerce-api-legacy.md`, `reports/audit-ecommerce-api-legacy.md` e `reports/refactor-ecommerce-api-legacy.md`

## 1. Resumo

| Campo | Resultado |
|---|---|
| Status geral | **PASS** (com ressalvas não bloqueantes) |
| Rotas do inventário testadas | **3/3** |
| Rotas aprovadas | **3/3 (100%)** |
| CRITICAL resolvidos | **2/2** |
| HIGH resolvidos | **4/4** |
| MEDIUM/LOW resolvidos | **7/7** |
| Checks estáticos | **OK** |
| Testes automatizados | **16/16 passando** |
| Boot (`npm start`) | **OK** |
| Revalidação SEC-04 (regra expandida) | **OK — checkout IDOR corrigido** |
| Recomendação | **APROVADO COM RESSALVAS** |

A refatoração preservou os contratos de sucesso das três rotas inventariadas na Fase 1 e corrigiu todos os achados CRITICAL/HIGH da auditoria. As mudanças de contrato existentes (autenticação nas rotas administrativas e mensagem do DELETE) são deliberadas, exigidas pela auditoria e estão documentadas na Fase 3.

## 2. Contrato original vs atual

Contrato de referência: `reports/analysis-ecommerce-api-legacy.md` §2.4 — 3 rotas, entrypoint `src/app.js`, boot `npm start`.

| Rota original | Verbo/Path atual | Contrato original | Contrato atual | Veredito |
|---|---|---|---|---|
| Checkout | `POST /api/checkout` | `200 {"msg":"Sucesso","enrollment_id":N}`; `400` para recusa; `404` para curso ausente | Mantido. Novos `400` para payload inválido e para novo usuário sem `pwd`; `401 Credenciais inválidas` para conta existente sem senha/senha errada (SEC-04); `500` genérico em falha interna | **PASS** (contrato de sucesso preservado) |
| Relatório financeiro | `GET /api/admin/financial-report` | `200 [{course, revenue, students:[{student, paid}]}]` | Shape e semântica preservados; agora exige `Authorization: Bearer <ADMIN_TOKEN>` (`401`/`503` sem auth) | **PASS** (auth adicionada por SEC-04) |
| Exclusão de usuário | `DELETE /api/users/:id` | `200` com texto informando que matrículas/pagamentos ficaram no banco | `200 "Usuário deletado com sucesso."`; dependências removidas na mesma transação; `404` se não existir; `400` se `id` inválido | **PASS** (correção de integridade) |

- **Stack:** inalterada — Node.js/Express 4.22.1 + SQLite (`sqlite3` 5.1.7). Adicionado apenas `dotenv` 18.0.9 para carregar `.env`.
- **Entrypoint:** mantido em `src/app.js`; `package.json` mantém `main` e script `start`.
- **Banco:** continua SQLite em memória por default, agora com migrations e opção `DATABASE_PATH`.

## 3. Smoke test por endpoint

Ambiente: `PORT=3005 ADMIN_TOKEN=validation-token`, banco em memória recém-inicializado. Rotas de escrita exercitadas com `curl`.

| # | Método | Path | Status obtido | Resultado | Observação / evidência |
|---|---|---|---|---|---|
| 1 | POST | `/api/checkout` | `200` | **PASS** | `{"msg":"Sucesso","enrollment_id":2}` — contrato de sucesso preservado |
| 2 | POST | `/api/checkout` (cartão `5...`) | `400` | **PASS** | `Pagamento recusado` — regra original preservada |
| 3 | POST | `/api/checkout` (payload `{usr}`) | `400` | **PASS** | `Bad Request` — validação QUAL-02 |
| 4 | POST | `/api/checkout` (`c_id: 999`) | `404` | **PASS** | `Curso não encontrado` |
| 5 | POST | `/api/checkout` (novo usuário sem `pwd`) | `400` | **PASS** | `pwd é obrigatório para novo usuário` — mudança documentada |
| 6 | GET | `/api/admin/financial-report` (com token) | `200` | **PASS** | Array com `Clean Architecture`/`Docker`, receita e estudantes corretos |
| 7 | GET | `/api/admin/financial-report` (sem token) | `401` | **PASS** | `{"error":"Unauthorized"}` — SEC-04 |
| 8 | GET | `/api/admin/financial-report` (sem `ADMIN_TOKEN` no processo) | `503` | **PASS** | `{"error":"Admin authentication is not configured"}` — fail-closed |
| 9 | DELETE | `/api/users/1` (com token) | `200` | **PASS** | `Usuário deletado com sucesso.` |
| 10 | GET | `/api/admin/financial-report` (após DELETE) | `200` | **PASS** | Curso `Clean Architecture` com `revenue: 0` e `students: []` — sem órfãos |
| 11 | DELETE | `/api/users/1` (repetido) | `404` | **PASS** | `Usuário não encontrado` |
| 12 | DELETE | `/api/users/abc` | `400` | **PASS** | `Bad Request` |
| 13 | GET | `/api/nope` | `404` | **PASS** | `{"error":"Not found"}` (middleware de 404) |
| 14 | POST | `/api/checkout` (processo sem `ADMIN_TOKEN`) | `200` | **PASS** | Checkout de novo usuário permanece público; a senha do titular é exigida apenas para conta existente (SEC-04) |

**Boot:** `npm start` subiu com `{"level":"info",...,"message":"Frankenstein LMS rodando na porta 3007...","port":3007}`.

### 3.1 Revalidação SEC-04 — regra expandida (2026-10-31)

A regra SEC-04 passou a cobrir rotas de cadastro/criação que aceitam identidade ou dono vindos do cliente. O gap residual era `POST /api/checkout`: o e-mail do body era aceito para criar matrícula/pagamento em nome de conta existente sem prova de posse (IDOR).

Ambiente: `PORT=3015 ADMIN_TOKEN=smoke-admin DATABASE_PATH=/tmp/opencode/sec04-smoke.db`, banco limpo.

| Cenário | Resultado obtido | Veredito |
|---|---|---|
| Novo usuário com `pwd` | `200 {"msg":"Sucesso","enrollment_id":2}` | **PASS** |
| Conta existente sem `pwd` | `401 Credenciais inválidas` | **PASS** (SEC-04) |
| Conta existente com `pwd` incorreta | `401 Credenciais inválidas` | **PASS** (SEC-04) |
| Conta existente com `pwd` correta | `200 {"msg":"Sucesso","enrollment_id":3}` | **PASS** (SEC-04) |
| Novo usuário sem `pwd` | `400 pwd é obrigatório para novo usuário` | **PASS** |
| `GET /api/admin/financial-report` sem token | `401 {"error":"Unauthorized"}` | **PASS** |
| `GET /api/admin/financial-report` com token | `200` relatório | **PASS** |
| `DELETE /api/users/1` sem token | `401 {"error":"Unauthorized"}` | **PASS** |

**Sem efeito colateral das tentativas negativas:** após os dois `401`, o relatório manteve apenas as matrículas legítimas — `Clean Architecture` com receita `1994` (Leonan + Alice) e `Docker` com `497` (Alice). Nenhuma matrícula extra foi criada em nome da conta alvo.

## 4. Verificação estática

| Check | Resultado | Evidência |
|---|---|---|
| Estrutura alvo presente | **OK** | `src/{config,database,migrations,models,repositories,services,controllers,routes,middleware,validators,utils,errors}` |
| Rotas separadas do entrypoint | **OK** | `src/routes/*.js`; `src/app.js` apenas compõe com `app.use('/api', createRoutes(...))` |
| Controllers sem SQL/regra pesada | **OK** | `grep` por SQL em `src/controllers` → nenhum; 42 LOC somados nos 3 controllers |
| Services sem SQL/HTTP | **OK** | `grep` por SQL/`req.`/`res.` em `src/services` → nenhum |
| Repositories sem HTTP | **OK** | `grep` por `req.`/`res.`/`express` em `src/repositories` → nenhum |
| Rotas não importam services/repositories | **OK** | `grep` em `src/routes` → nenhum import direto de services/repositories |
| Queries parametrizadas | **OK** | Todas as queries usam `?` + bindings; `ReportRepository` usa template literal apenas para SQL estático, sem `${}` |
| Segredos hardcoded | **OK** | `grep` por `password=`/`api_key=`/`token=`/`pk_live`/`secret=` em `src` e `.env.example` → nenhum valor real |
| Configuração centralizada | **OK** | `src/config/index.js` lê `process.env` + `dotenv`; segredos obrigatórios falham em produção |
| Arquivos órfãos | **OK** | `src/AppManager.js` e `src/utils.js` removidos; nenhum import/referência remanescente |
| Migrations versionadas | **OK** | `src/database/migrations/001_initial_schema.sql`; runner `src/database/migrator.js` com `schema_migrations` |
| Sem captura genérica engolindo erro | **OK** | `catch` apenas em `asyncHandler` (delega ao error handler), rollback (reanexa erro) e boot (loga e falha) |
| Testes presentes | **OK** | `tests/api.test.js`, `tests/password.test.js`; `package.json` com script `test` |
| Dependências coerentes | **OK** | `npm ls --depth=0`: `dotenv@18.0.9`, `express@4.22.1`, `sqlite3@5.1.7` |

## 5. Cruzamento com a auditoria (CRITICAL/HIGH)

### CRITICAL

| Achado | Status | Evidência da correção |
|---|---|---|
| **SEC-02** — Credenciais hardcoded | **RESOLVIDO** | `src/config/index.js:1-30` lê `ADMIN_TOKEN`/`PAYMENT_GATEWAY_KEY` de `process.env`; `optionalSecret` falha em produção (`:5-9`); nenhum literal de senha/chave no `grep`; `.env.example` contém apenas placeholders. |
| **SEC-03** — Criptografia fraca | **RESOLVIDO** | `src/utils/password.js:3-28` usa `scrypt` com salt aleatório de 16 bytes, chave de 64 bytes e `timingSafeEqual`; seed em `src/database/schema.js:12` usa senha aleatória e grava somente hash; `tests/password.test.js` valida salt/verificação. |

### HIGH

| Achado | Status | Evidência da correção |
|---|---|---|
| **SEC-04** — Rota sem auth | **RESOLVIDO** | `src/middleware/auth.js:11-21` valida `Bearer` em tempo constante; aplicado em `src/routes/adminRoutes.js:5` e `src/routes/userRoutes.js:5`. Smoke test: `401` sem token, `503` sem `ADMIN_TOKEN`, `200` com token. No checkout, `src/services/CheckoutService.js:38-48` exige `pwd` válido quando o e-mail já existe (`401` sem senha/senha errada) e nunca aceita id/role do body; novo usuário continua público. Evidência: seção 3.1. |
| **SEC-06** — Log com dados sensíveis | **RESOLVIDO** | `src/services/CheckoutService.js:51-57` loga apenas `cardLast4`, `userId`, `courseId` e status; nenhuma ocorrência de log de `paymentGatewayKey` ou cartão completo. |
| **ARCH-01** — Lógica de negócio no Controller | **RESOLVIDO** | Regras em `CheckoutService` (`src/services/CheckoutService.js:34-82`), `FinancialReportService` (`:8-31`) e `UserService` (`:11-24`); controllers somam 42 LOC e apenas validam/orquestram/serializam. |
| **ARCH-02** — Acesso a dados no Controller | **RESOLVIDO** | SQL isolado em 6 repositories (`src/repositories/*.js`); `grep` confirma ausência de SQL em controllers e services. |

### MEDIUM/LOW (não bloqueantes)

| Achado | Status | Evidência |
|---|---|---|
| PERF-01 — N+1 | **RESOLVIDO** | `ReportRepository.js:7-24` usa um único `LEFT JOIN`; agregação em `FinancialReportService.js:8-31`; smoke test retornou receita/estudantes corretos. |
| QUAL-02 — Validação ausente | **RESOLVIDO** | `checkoutValidator.js` e `idValidator.js`; `400` observado para payload malformado, cartão inválido e `id` não numérico. |
| QUAL-03 — Erro genérico/engolido | **RESOLVIDO** | `middleware/errorHandler.js` central; `connection.js:30-46` faz rollback; nenhum `catch` vazio; `500` genérico sem stack. |
| QUAL-04 — Estado global mutável | **RESOLVIDO** | `globalCache`/`totalRevenue` removidos; dependências via `container.js`; nenhum estado mutável de módulo. |
| QUAL-06 — Sem migrations | **RESOLVIDO** | `src/database/migrations/001_initial_schema.sql` + `migrator.js`; idempotência verificada: `schema_migrations` contém 1 registro e `users=1` após duas inicializações. |
| QUAL-07 — Config hardcoded | **RESOLVIDO** | `src/config/index.js` usa env para porta, banco, token e chave; `.env.example` documenta as variáveis. |
| QUAL-08 — Sem testes | **RESOLVIDO** | 16 testes em `tests/`, todos passando; cobrem rotas, auth admin, posse no checkout (SEC-04), validação, relatório, cascade delete e hash. |

**Resultado do cruzamento:** 13/13 achados resolvidos (2 CRITICAL, 4 HIGH, 4 MEDIUM, 3 LOW). Nenhum CRITICAL/HIGH permanece aberto. A reauditoria de 2026-10-31, com a regra SEC-04 expandida, encontrou e corrigiu um gap adicional de IDOR no checkout (seção 3.1).

## 6. Riscos e ressalvas

1. **Autenticação simplificada:** token admin estático, compartilhado e sem expiração/revogação/RBAC. Para produção, integrar identidade (JWT/OIDC), roles e rotação de token. No checkout, a prova de posse é a senha do titular; não há verificação de e-mail no cadastro público, então um terceiro ainda pode pré-registrar um e-mail conhecido (account pre-hijacking) — exigir confirmação de e-mail.
2. **Mudanças de contrato deliberadas:** rotas administrativas agora exigem auth; DELETE retorna mensagem diferente e `404` para ausente; novo usuário sem `pwd` retorna `400`; validação é mais estrita; erros internos são genéricos. Clientes precisam ser ajustados.
3. **Pagamento simulado:** a aprovação continua baseada em `card.startsWith('4')`; `PAYMENT_GATEWAY_KEY` está reservada para integração real. Faltam tokenização, PCI e tratamento de falhas do provedor.
4. **Persistência:** default em memória (`:memory:`); migrations prontas, mas não há backup/restore, retenção ou operação de banco externo.
5. **Operação:** sem rate limiting, CORS, `helmet`, timeouts, correlação de logs, métricas, tracing ou CI/CD.
6. **Testes:** cobrem caminhos principais, mas não concorrência, falhas de banco, carga ou cobertura mínima.
7. **Exclusão:** hard delete; avaliar soft delete/retenção conforme LGPD.
8. **Clientes HTTP:** `api.http` usa `{{$processEnv ADMIN_TOKEN}}`, que pode não funcionar em todos os clientes REST.

Nenhuma dessas ressalvas representa regressão funcional ou falha crítica; são débitos operacionais/evolutivos.

## 7. Recomendação final

**APROVADO COM RESSALVAS.**

A refatoração atende aos critérios de aceitação: a aplicação sobe, as 3 rotas do inventário mantêm path/verbo e contratos de sucesso, todos os CRITICAL/HIGH foram resolvidos com evidência e a suíte automatizada passa 16/16. A revalidação SEC-04 com a regra expandida confirmou a correção do IDOR no checkout (seção 3.1). As ressalvas acima são não bloqueantes e devem entrar no backlog de evolução.

Ações recomendadas (prioridade):

1. Substituir o token estático por autenticação com identidade/roles e rotação.
2. Integrar o gateway de pagamento real com tokenização e conformidade PCI.
3. Configurar `DATABASE_PATH` persistente + backup/restore.
4. Adicionar rate limiting, `helmet`, CORS restritivo e observabilidade.
5. Adicionar CI/CD com `npm ci`, `npm test` e lint.
6. Ampliar testes para concorrência, falhas de banco e cobertura mínima.

## 8. Notas e evidências

### Comandos executados

```bash
# Boot (comando da Fase 1)
PORT=3007 ADMIN_TOKEN=validation-token LOG_LEVEL=info timeout 5s npm start
# -> {"level":"info",...,"message":"Frankenstein LMS rodando na porta 3007...","port":3007}

# Testes
npm test
# -> tests 16 | pass 16 | fail 0

# Smoke test
PORT=3005 ADMIN_TOKEN=validation-token LOG_LEVEL=error node src/app.js
# -> POST/GET/DELETE exercitados conforme tabela da seção 3

# Revalidação SEC-04 (regra expandida)
PORT=3015 ADMIN_TOKEN=smoke-admin LOG_LEVEL=error DATABASE_PATH=/tmp/opencode/sec04-smoke.db node src/app.js
# -> novo usuário com pwd: 200
# -> conta existente sem pwd: 401 Credenciais inválidas
# -> conta existente com pwd errada: 401 Credenciais inválidas
# -> conta existente com pwd correta: 200
# -> GET admin sem token: 401; com token: 200
# -> DELETE sem token: 401; novo usuário sem pwd: 400

# Fail-closed sem ADMIN_TOKEN
PORT=3006 LOG_LEVEL=error node src/app.js
# -> GET admin: 503; POST checkout: 200

# Verificações estáticas
grep -rn "SELECT|INSERT|UPDATE|DELETE FROM" src/controllers   # nenhum
grep -rn "SELECT|INSERT|UPDATE|DELETE FROM|req.|res." src/services  # nenhum
grep -rn "req.|res.|express" src/repositories                 # nenhum
grep -rn 'db\.(run|get|all)\(`[^`]*\$\{' src                  # nenhum
grep -rniE "password=...|api_key=...|token=...|pk_live|secret=..." src .env.example  # nenhum
npm ls --depth=0
# dotenv@18.0.9, express@4.22.1, sqlite3@5.1.7
```

### Integridade do repositório

- `src/AppManager.js` e `src/utils.js` deletados; nenhuma referência remanescente.
- `git status` contém apenas arquivos esperados da refatoração (`src/*` novos, `README.md`, `api.http`, `package.json`, `package-lock.json`, `reports/`), além de arquivos preexistentes fora deste projeto (`../README_.md`, `../code-smells-project/...`) que não foram tocados.
- Nenhum arquivo de código-fonte foi alterado durante a Fase 4; apenas leitura, execução e este relatório.
- Migrations idempotentes: duas execuções de `initializeSchema` em banco limpo resultaram em `schema_migrations = ["001_initial_schema.sql"]` e `users = 1`.
- `dotenv` carrega `.env` quando presente; variáveis já definidas no ambiente têm precedência.
