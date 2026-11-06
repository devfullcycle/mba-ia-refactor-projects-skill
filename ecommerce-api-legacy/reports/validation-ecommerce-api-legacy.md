# Validation Report — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 4 — Validação Pós-Refatoração).
> Data: 2026-11-05 | Atualizado: 2026-11-05 (Etapa 7 — revalidação SEC-02/03/04/06)
> Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
> Baseado em: `reports/analysis-ecommerce-api-legacy.md`, `reports/audit-ecommerce-api-legacy.md` e `reports/refactor-ecommerce-api-legacy.md`

## 1. Resumo

| Campo | Resultado |
|---|---|
| Status geral | **PASS** |
| Rotas do inventário testadas | **3/3** |
| Rotas aprovadas | **3/3 (100%)** |
| CRITICAL resolvidos | **2/2** |
| HIGH resolvidos | **4/4** |
| CRITICAL pendentes | **0** |
| HIGH pendentes | **0** |
| MEDIUM/LOW resolvidos | **7/7** |
| Checks estáticos | **OK** |
| Testes automatizados | **16/16 passando** |
| Smoke HTTP manual | **14/14 cenários com status esperado** |
| Boot (`npm start`) | **OK** |
| Fail-closed sem `ADMIN_TOKEN` | **OK** (rotas admin → 503) |
| Banco em repouso | **OK** (somente hash scrypt) |
| Logs | **OK** (sem PAN, chave ou senha) |
| Recomendação | **APROVADO** |

**Gate da Etapa 7:**

- `Critical resolved: 2/2`
- `High resolved: 4/4`
- `Partial critical/high: 0`
- `SEC-02: RESOLVIDO`
- `SEC-03: RESOLVIDO`
- `SEC-04: RESOLVIDO`
- `SEC-06: RESOLVIDO`
- `Tests: 16/16`

A refatoração preservou os contratos de sucesso das três rotas inventariadas
na Fase 1 e mantém corrigidos todos os achados CRITICAL/HIGH da auditoria.
Nesta reexecução foram reverificados os quatro achados de segurança exigidos
pela Etapa 7 — credenciais, hash de senha, autorização admin/IDOR no checkout e
logs — com evidência de código, banco em repouso, HTTP real e captura de log.

## 2. Contrato original vs atual

Contrato de referência: `reports/analysis-ecommerce-api-legacy.md` §2.4 — 3 rotas,
entrypoint `src/app.js`, boot `npm start`.

| Rota original | Verbo/Path atual | Contrato original | Contrato atual | Veredito |
|---|---|---|---|---|
| Checkout | `POST /api/checkout` | `200 {"msg":"Sucesso","enrollment_id":N}`; `400` para recusa; `404` para curso ausente | Mantido. Novos `400` para payload inválido e para novo usuário sem `pwd`; `401 Credenciais inválidas` para conta existente sem senha/senha errada (SEC-04); `500` genérico em falha interna | **PASS** (contrato de sucesso preservado) |
| Relatório financeiro | `GET /api/admin/financial-report` | `200 [{course, revenue, students:[{student, paid}]}]` | Shape e semântica preservados; agora exige `Authorization: Bearer <ADMIN_TOKEN>` (`401` sem token, `503` sem `ADMIN_TOKEN`) | **PASS** (auth adicionada por SEC-04) |
| Exclusão de usuário | `DELETE /api/users/:id` | `200` com texto informando que matrículas/pagamentos ficaram no banco | `200 "Usuário deletado com sucesso."`; dependências removidas na mesma transação; `404` se não existir; `400` se `id` inválido; exige admin | **PASS** (correção de integridade + SEC-04) |

- **Stack:** inalterada — Node.js/Express 4.22.1 + SQLite (`sqlite3` 5.1.7). Adicionado apenas `dotenv` 18.0.9 para carregar `.env`.
- **Entrypoint:** mantido em `src/app.js`; `package.json` mantém `main` e script `start`.
- **Banco:** continua SQLite em memória por default, agora com migrations e opção `DATABASE_PATH`.

## 3. Smoke test por endpoint e caminhos de erro

Ambiente principal: `NODE_ENV=development PORT=5070 DATABASE_PATH=/tmp/opencode/ec-etapa7.db ADMIN_TOKEN=etapa7-admin PAYMENT_GATEWAY_KEY=etapa7-gateway-key LOG_LEVEL=debug node src/app.js`.

| # | Método | Path / cenário | Status | Resultado | Observação |
|---|---|---|---|---|---|
| 1 | POST | `/api/checkout` — novo usuário com `pwd` | 200 | **PASS** | `{"msg":"Sucesso","enrollment_id":2}` |
| 2 | POST | `/api/checkout` — conta existente sem `pwd` | 401 | **PASS** | `Credenciais inválidas` — SEC-04 |
| 3 | POST | `/api/checkout` — conta existente com `pwd` errada | 401 | **PASS** | `Credenciais inválidas` — SEC-04 |
| 4 | POST | `/api/checkout` — conta existente com `pwd` correta | 200 | **PASS** | `{"msg":"Sucesso","enrollment_id":3}` — SEC-04 |
| 5 | POST | `/api/checkout` — cartão `5...` | 400 | **PASS** | `Pagamento recusado` — regra original preservada |
| 6 | POST | `/api/checkout` — payload `{usr}` | 400 | **PASS** | `Bad Request` — QUAL-02 |
| 7 | POST | `/api/checkout` — `c_id: 999` | 404 | **PASS** | `Curso não encontrado` |
| 8 | GET | `/api/admin/financial-report` — sem token | 401 | **PASS** | `{"error":"Unauthorized"}` — SEC-04 |
| 9 | GET | `/api/admin/financial-report` — token inválido | 401 | **PASS** | `{"error":"Unauthorized"}` — SEC-04 |
| 10 | GET | `/api/admin/financial-report` — com token | 200 | **PASS** | Relatório com `Clean Architecture`/`Docker`, receita e estudantes corretos |
| 11 | DELETE | `/api/users/2` — sem token | 401 | **PASS** | `{"error":"Unauthorized"}` — SEC-04 |
| 12 | DELETE | `/api/users/abc` — com token | 400 | **PASS** | `Bad Request` |
| 13 | DELETE | `/api/users/2` — com token | 200 | **PASS** | `Usuário deletado com sucesso.` |
| 14 | DELETE | `/api/users/999` — com token | 404 | **PASS** | `Usuário não encontrado` |

**Fail-closed sem `ADMIN_TOKEN`** (processo separado, porta 5071):

| Cenário | Resultado obtido | Veredito |
|---|---|---|
| `GET /api/admin/financial-report` sem `ADMIN_TOKEN` | `503 {"error":"Admin authentication is not configured"}` | **PASS** (SEC-04) |
| `POST /api/checkout` novo usuário sem `ADMIN_TOKEN` | `200 {"msg":"Sucesso","enrollment_id":2}` | **PASS** (checkout público preservado) |

**Boot e testes:**

- `npm start` subiu sem erros, com log JSON `Frankenstein LMS rodando na porta ...`.
- `npm test` → **16/16 testes passando** (0 falhas).
- `NODE_ENV=production node src/app.js` sem segredos → `Error: Missing required environment variable: ADMIN_TOKEN`, exit 1 (SEC-02 fail-fast).

## 4. Verificação de segurança (SEC-02/03/04/06)

### 4.1 SEC-02 — Credenciais somente via ambiente

| Check | Resultado | Evidência |
|---|---|---|
| Nenhum literal de credencial em `src` | **OK** | `grep` por `admin_master`, `senha_super_secreta_prod_123`, `pk_live_1234567890abcdef`, `123456` → nenhuma ocorrência |
| `.env.example` apenas com placeholders | **OK** | `ADMIN_TOKEN=replace-with-a-strong-random-token`, `PAYMENT_GATEWAY_KEY=replace-with-gateway-key` |
| Config centralizada | **OK** | `src/config/index.js` lê `process.env` via `dotenv`; valores não-sensíveis têm default |
| Produção falha sem segredo | **OK** | Boot com `NODE_ENV=production` sem `ADMIN_TOKEN` aborta com exit 1 |
| Segredo não é logado nem retornado | **OK** | Nenhuma resposta HTTP contém token/chave; log capturado não contém `etapa7-gateway-key` |

### 4.2 SEC-03 — Hash de senha

| Check | Resultado | Evidência |
|---|---|---|
| Algoritmo com salt e custo | **OK** | `src/utils/password.js` usa `crypto.scryptSync` com salt aleatório de 16 bytes e chave de 64 bytes |
| Verificação em tempo constante | **OK** | `crypto.timingSafeEqual` após derivar a chave |
| Sem criptografia reversível | **OK** | Nenhum `base64`/hash truncado; formato `scrypt$salt$hash` |
| Seed sem texto puro | **OK** | `src/database/schema.js` gera senha aleatória e grava apenas `hashPassword(...)` |
| Banco em repouso | **OK** | `users.pass` de `leonan@fullcycle.com.br` = `scrypt$...` (168 caracteres); nenhum valor igual a `123`, `123456` ou senha informada |
| Teste dedicado | **OK** | `tests/password.test.js` valida salt distinto, verificação correta e rejeição de hash inválido |

### 4.3 SEC-04 — Autorização admin e posse no checkout

| Check | Resultado | Evidência |
|---|---|---|
| Relatório financeiro exige admin | **OK** | `requireAdmin` em `src/routes/adminRoutes.js`; `401` sem token, `200` com token |
| DELETE exige admin | **OK** | `requireAdmin` em `src/routes/userRoutes.js`; `401` sem token, `200` com token |
| Sem `ADMIN_TOKEN` falha fechado | **OK** | `503` nas rotas administrativas |
| Token comparado em tempo constante | **OK** | `crypto.timingSafeEqual` em `src/middleware/auth.js` |
| Checkout não aceita identidade de terceiro | **OK** | Conta existente exige `pwd` do titular; sem senha/errada → `401`; correta → `200` |
| Dono não vem do body | **OK** | `usuario_id`/`owner_id`/`role` não são lidos; o dono é `existingUser.id` ou o usuário recém-criado |
| Sem efeito colateral em tentativa negativa | **OK** | Os dois `401` não criaram matrícula/pagamento extra |

### 4.4 SEC-06 — Logs sem dados sensíveis

Log capturado com `LOG_LEVEL=debug` durante todos os cenários:

| Valor proibido | Presente no log? |
|---|---|
| PAN completo `4111222233334444` | **não** |
| Chave do gateway `etapa7-gateway-key` | **não** |
| Senha `senha-forte-alice` | **não** |
| Literal legado `123456` | **não** |

O log de pagamento contém apenas metadados permitidos: `event`, `userId`,
`courseId`, `cardLast4` (4 últimos dígitos) e `status`. Nenhuma senha, PAN
completo ou chave do gateway é registrada.

## 5. Verificação estática

| Check | Resultado | Evidência |
|---|---|---|
| Estrutura alvo presente | **OK** | `src/{config,database,migrations,models,repositories,services,controllers,routes,middleware,validators,utils,errors}` |
| Rotas separadas do entrypoint | **OK** | `src/routes/*.js`; `src/app.js` apenas compõe com `app.use('/api', createRoutes(...))` |
| Controllers sem SQL/regra pesada | **OK** | `grep` por SQL em `src/controllers` → nenhum |
| Services sem SQL/HTTP | **OK** | `grep` por SQL/`req.`/`res.` em `src/services` → nenhum |
| Repositories sem HTTP | **OK** | `grep` por `req.`/`res.`/`express` em `src/repositories` → nenhum |
| Queries parametrizadas | **OK** | Todas usam `?` + bindings; `ReportRepository` usa template literal apenas para SQL estático |
| Segredos hardcoded | **OK** | Nenhum valor real em `src` ou `.env.example` |
| Configuração centralizada | **OK** | `src/config/index.js` lê `process.env`; segredos obrigatórios falham em produção |
| Arquivos órfãos | **OK** | `src/AppManager.js` e `src/utils.js` removidos, sem referências |
| Migrations versionadas | **OK** | `src/database/migrations/001_initial_schema.sql` + `migrator.js` com `schema_migrations` |
| Sem captura genérica engolindo erro | **OK** | `catch` apenas em `asyncHandler`, rollback e boot |
| Testes presentes | **OK** | `tests/api.test.js`, `tests/password.test.js`; 16 testes |
| Dependências coerentes | **OK** | `dotenv@18.0.9`, `express@4.22.1`, `sqlite3@5.1.7` |

## 6. Cruzamento com a auditoria (CRITICAL/HIGH)

### CRITICAL

| Achado | Status | Evidência da correção |
|---|---|---|
| **SEC-02** — Credenciais hardcoded | **RESOLVIDO** | `src/config/index.js` lê `ADMIN_TOKEN`/`PAYMENT_GATEWAY_KEY` de `process.env`; produção falha no boot sem eles; nenhum literal no `grep`; `.env.example` apenas com placeholders. |
| **SEC-03** — Criptografia fraca | **RESOLVIDO** | `src/utils/password.js` usa `scrypt` com salt aleatório de 16 bytes, chave de 64 bytes e `timingSafeEqual`; seed usa senha aleatória gravada apenas como hash; banco em repouso contém apenas `scrypt$...`; `tests/password.test.js` valida salt/verificação. |

### HIGH

| Achado | Status | Evidência da correção |
|---|---|---|
| **SEC-04** — Rota sem auth | **RESOLVIDO** | `requireAdmin` valida `Bearer` em tempo constante em `adminRoutes.js` e `userRoutes.js`; `401` sem token, `503` sem `ADMIN_TOKEN`, `200` com token. Checkout exige senha do titular para conta existente (`401` sem senha/errada, `200` com correta) e nunca aceita id/role do body. |
| **SEC-06** — Log com dados sensíveis | **RESOLVIDO** | `CheckoutService` loga apenas `cardLast4`, `userId`, `courseId` e status; captura de log com `LOG_LEVEL=debug` não contém PAN completo, chave do gateway nem senha. |
| **ARCH-01** — Lógica de negócio no Controller | **RESOLVIDO** | Regras em `CheckoutService`, `FinancialReportService` e `UserService`; controllers validam/orquestram/serializam. |
| **ARCH-02** — Acesso a dados no Controller | **RESOLVIDO** | SQL isolado em 6 repositories; `grep` confirma ausência de SQL em controllers e services. |

**Resultado: 2/2 CRITICAL e 4/4 HIGH resolvidos. Nenhum item CRITICAL/HIGH pendente.**

### MEDIUM/LOW (não bloqueiam)

| Achado | Status | Evidência |
|---|---|---|
| PERF-01 — N+1 | **RESOLVIDO** | `ReportRepository` usa um único `LEFT JOIN`; agregação em `FinancialReportService`; smoke retornou receita/estudantes corretos. |
| QUAL-02 — Validação ausente | **RESOLVIDO** | `checkoutValidator.js` e `idValidator.js`; `400` para payload malformado, cartão inválido e `id` não numérico. |
| QUAL-03 — Erro genérico/engolido | **RESOLVIDO** | `middleware/errorHandler.js` central; `connection.js` faz rollback; nenhum `catch` vazio; `500` genérico sem stack. |
| QUAL-04 — Estado global mutável | **RESOLVIDO** | `globalCache`/`totalRevenue` removidos; dependências via `container.js`; nenhum estado mutável de módulo. |
| QUAL-06 — Sem migrations | **RESOLVIDO** | `001_initial_schema.sql` + `migrator.js`; idempotência verificada; `schema_migrations` com 1 registro. |
| QUAL-07 — Config hardcoded | **RESOLVIDO** | `src/config/index.js` usa env para porta, banco, token e chave; `.env.example` documenta as variáveis. |
| QUAL-08 — Sem testes | **RESOLVIDO** | 16 testes em `tests/`, todos passando; cobrem rotas, auth admin, posse no checkout, validação, relatório, cascade delete e hash. |

**Resultado consolidado: 13/13 achados resolvidos (2 CRITICAL, 4 HIGH, 4 MEDIUM, 3 LOW).**

## 7. Riscos e ressalvas

1. **Autenticação simplificada:** token admin estático, compartilhado e sem
   expiração/revogação/RBAC multiusuário. Para produção, integrar identidade
   (JWT/OIDC), roles e rotação de token. No checkout, a prova de posse é a senha
   do titular; não há verificação de e-mail no cadastro público, então um
   terceiro ainda pode pré-registrar um e-mail conhecido (account
   pre-hijacking) — exigir confirmação de e-mail.
2. **Mudanças de contrato deliberadas:** rotas administrativas agora exigem
   auth; DELETE retorna mensagem diferente e `404` para ausente; novo usuário
   sem `pwd` retorna `400`; validação é mais estrita; erros internos são
   genéricos.
3. **Pagamento simulado:** a aprovação continua baseada em `card.startsWith('4')`;
   `PAYMENT_GATEWAY_KEY` está reservada para integração real. Faltam
   tokenização, PCI e tratamento de falhas do provedor.
4. **Persistência:** default em memória (`:memory:`); migrations prontas, mas
   não há backup/restore, retenção ou operação de banco externo.
5. **Operação:** sem rate limiting, CORS, `helmet`, timeouts, correlação de
   logs, métricas, tracing ou CI/CD.
6. **Testes:** cobrem caminhos principais, mas não concorrência, falhas de banco,
   carga ou cobertura mínima.
7. **Exclusão:** hard delete; avaliar soft delete/retenção conforme LGPD.

Nenhuma dessas ressalvas representa regressão funcional ou falha CRITICAL/HIGH.

## 8. Recomendação final

**APROVADO**

A refatoração atende ao gate da Etapa 7: a aplicação sobe, as 3 rotas do
inventário mantêm path/verbo e contratos de sucesso, **2/2 CRITICAL** e
**4/4 HIGH** estão resolvidos com evidência de código e execução, a suíte
automatizada passa **16/16** e o smoke HTTP cobre 14 cenários com os status
esperados. O banco em repouso contém apenas hashes scrypt e os logs não expõem
PAN completo, chave de pagamento nem senha.

Ações recomendadas (não bloqueantes, backlog de evolução):

1. Substituir o token estático por autenticação com identidade/roles e rotação.
2. Integrar o gateway de pagamento real com tokenização e conformidade PCI.
3. Configurar `DATABASE_PATH` persistente + backup/restore.
4. Adicionar rate limiting, `helmet`, CORS restritivo e observabilidade.
5. Adicionar CI/CD com `npm ci`, `npm test` e lint.
6. Ampliar testes para concorrência, falhas de banco e cobertura mínima.

## 9. Notas e evidências

### Comandos executados

```bash
# Testes
npm test
# -> tests 16 | pass 16 | fail 0

# Boot + smoke (banco persistente para inspeção)
NODE_ENV=development PORT=5070 DATABASE_PATH=/tmp/opencode/ec-etapa7.db \
  ADMIN_TOKEN=etapa7-admin PAYMENT_GATEWAY_KEY=etapa7-gateway-key \
  LOG_LEVEL=debug node src/app.js

# Fail-closed sem ADMIN_TOKEN
NODE_ENV=development PORT=5071 DATABASE_PATH=/tmp/opencode/ec-etapa7-noauth.db \
  LOG_LEVEL=error node src/app.js
# -> GET /api/admin/financial-report: 503
# -> POST /api/checkout: 200

# Fail-fast em produção
NODE_ENV=production PORT=5072 node src/app.js
# -> Error: Missing required environment variable: ADMIN_TOKEN (exit 1)

# Verificações estáticas
grep -rn "SELECT|INSERT|UPDATE|DELETE FROM" src/controllers          # nenhum
grep -rn "SELECT|INSERT|UPDATE|DELETE FROM|req.|res." src/services   # nenhum
grep -rn "req.|res.|express" src/repositories                        # nenhum
grep -rniE "password=|api_key=|token=|pk_live|secret=" src .env.example  # nenhum
```

- **Banco em repouso:** `/tmp/opencode/ec-etapa7.db` → `users.pass` com prefixo `scrypt$` e 168 caracteres; nenhum texto puro.
- **Logs:** `/tmp/opencode/ec-etapa7.log` sem PAN completo, chave do gateway ou senha; metadado `cardLast4` presente.
- **Contrato de referência:** `reports/analysis-ecommerce-api-legacy.md` §2.4 (3 rotas).
- **Achados de referência:** `reports/audit-ecommerce-api-legacy.md` §2 e critérios §2.1.
- **Fase 4:** nenhum arquivo de código-fonte foi modificado nesta etapa de validação (somente verificação + relatórios).
- **Limpeza:** servidores das portas 5070/5071 encerrados; bancos e logs de execução em `/tmp/opencode`.
