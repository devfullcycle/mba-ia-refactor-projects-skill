# Validação — Projeto 2 (ecommerce-api-legacy)

Protocolo de `references/validation.md`: baseline capturado antes de qualquer modificação,
refatoração aplicada, mesma bateria reexecutada e comparada.

- Runtime: Node.js v20.20.2, Express 4.22.1, sqlite3 5.1.7
- Antes: `node src/app.js` — Após: `npm start` (`node server.js`)
- Banco `:memory:` — os dois lados partem do mesmo estado (schema + seed a cada boot)
- Bateria: 8 chamadas cobrindo os 3 endpoints, mais 5 checagens adicionais de autorização

## Resultado

```
Validation
  ✓ Application boots without errors        (log estruturado, sem warning)
  ✓ 5/5 chamadas de checkout com status idêntico ao baseline
  ✓ 3/3 diferenças são intencionais (rotas administrativas passaram a exigir credencial)
  ✓ Payload de sucesso e do relatório financeiro idênticos ao baseline
  ✓ No hardcoded secrets remaining          (grep vazio em src/ e server.js)
  ✓ Layer boundaries respected              (sem SQL fora de models/database, sem res.* em models/services)
  ✓ Zero ocorrências de PAN de cartão ou chave de gateway no log
  ✓ require de src/app sem efeito colateral de I/O
```

## Comparação status a status

| Chamada | Baseline | Após (sem credencial) | Após (com `x-api-key`) | Situação |
|---|---|---|---|---|
| POST /api/checkout (usuário novo) | 200 | 200 | — | igual |
| POST /api/checkout (usuário existente) | 200 | 200 | — | igual |
| POST /api/checkout (pagamento recusado) | 400 | 400 | — | igual |
| POST /api/checkout (payload incompleto) | 400 | 400 | — | igual |
| POST /api/checkout (curso inexistente) | 404 | 404 | — | igual |
| GET /api/admin/financial-report | 200 | **401** | 200 | protegido — finding 9 |
| DELETE /api/users/1 | 200 | **401** | 200 | protegido — finding 9 |
| GET /api/admin/financial-report (após deleção) | 200 | **401** | 200 | protegido — finding 9 |

Checagens adicionais de autorização:

| Checagem | Resultado |
|---|---|
| `x-api-key` inválida em rota administrativa | 401 ✓ |
| `DELETE /api/users/999` (inexistente, com credencial) | 404 ✓ (antes: 200 silencioso) |
| Checkout de conta nova sem `pwd` | 400 ✓ (antes: criava a conta com senha `123456`) |

## Diferenças intencionais de contrato

| Mudança | Antes | Depois | Finding |
|---|---|---|---|
| Rotas administrativas | abertas a qualquer cliente | exigem `x-api-key`; negam por default quando `ADMIN_API_KEY` não está configurada | 9 |
| Senha ausente no checkout | conta criada com `"123456"` | 400 exigindo senha de ≥6 caracteres | 4 |
| Corpo das respostas de erro | `text/plain` (`"Pagamento recusado"`) | JSON (`{"error":"Pagamento recusado"}`) | 11 |
| `DELETE /api/users/:id` | 200 declarando que deixou órfãos | 200 com remoção em cascata; 404 se o usuário não existe | 8 |
| Relatório após deleção | listava matrículas órfãs como `student: "Unknown"` | as matrículas do usuário removido não existem mais | 8 |
| Pagamento recusado para conta nova | criava o usuário antes de recusar | não persiste nada (cobrança ocorre antes da transação) | 5 |

## Evidência das correções

### Payload de sucesso preservado

```console
# baseline e após — idênticos
{"msg":"Sucesso","enrollment_id":2}
```

### Relatório financeiro preservado (autenticado)

```console
# baseline
[{"course":"Clean Architecture","revenue":1994,"students":[{"student":"Leonan","paid":997},
  {"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,
  "students":[{"student":"Guilherme","paid":497}]}]

# após — byte a byte igual, mas resolvido em 1 query em vez de ~1+N+2M
```

### Integridade referencial (finding 8)

```console
# ANTES — após DELETE /api/users/1, matrículas e pagamentos órfãos permanecem
[{"course":"Clean Architecture","revenue":1994,
  "students":[{"student":"Unknown","paid":997},{"student":"Unknown","paid":997}]}, ...]

# DEPOIS — ON DELETE CASCADE remove as dependências
[{"course":"Clean Architecture","revenue":0,"students":[]},
 {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
```

### Vazamento de dados de cartão (finding 3)

```console
# ANTES — log do servidor durante o baseline
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
Processando cartão 4555666677778888 na chave pk_live_1234567890abcdef

# DEPOIS — apenas os 4 últimos dígitos, sem a chave do gateway
{"ts":"2026-07-24T21:24:37.232Z","level":"info","message":"Cobrança processada",
 "context":{"cardLast4":"4444","amount":497,"status":"PAID","gateway":"simulado"}}

# grep por PAN completo ou pk_live no log após a refatoração
$ grep -cE "4111222233334444|4555666677778888|pk_live" server.log
0
```

## Checagens estruturais

| Checagem | Resultado |
|---|---|
| Segredo literal em `src/`/`server.js` | vazio ✓ |
| SQL fora de `models/` e `database/` | vazio ✓ |
| `require('express')` ou `res.*` em `models/`/`services/` | vazio ✓ |
| `console.log` de diagnóstico | vazio ✓ |
| Estado global mutável (`let x = {}` em escopo de módulo) | vazio ✓ |
| Erro de callback ignorado / `self = this` | vazio ✓ |
| Transação (`BEGIN`/`ROLLBACK`) presente | ✓ `src/database/connection.js:58` |
| `ON DELETE CASCADE` no schema | ✓ `src/database/schema.js:29, 36` |
| `require` sem efeito colateral de I/O | ✓ |

## Log de boot após a refatoração

```json
{"ts":"2026-07-24T21:25:50.214Z","level":"info","message":"Banco populado com dados de demonstração"}
{"ts":"2026-07-24T21:25:50.218Z","level":"info","message":"Servidor iniciado",
 "context":{"service":"lms-api","port":3000,"env":"development","database":":memory:"}}
```

Sem `ADMIN_API_KEY` configurada, o boot emite aviso e as rotas administrativas respondem 401 —
o comportamento é fail closed, não fail open.

## Riscos residuais (fora do escopo dos findings, registrados por honestidade)

1. **Checkout não autentica o titular do e-mail.** Como no legado, informar o e-mail de uma
   conta existente matricula aquela conta (o `pwd` é ignorado quando o usuário já existe).
   Corrigir exigiria autenticação no fluxo de checkout, o que mudaria o contrato — ficou fora
   desta refatoração e está registrado aqui.
2. **Autorização administrativa por chave estática.** `x-api-key` é suficiente para fechar a
   rota (fail closed, comparação em tempo constante), mas não substitui autenticação de
   usuário com papéis. O middleware está isolado e pode ser trocado sem tocar em controller.
3. **Credencial de demonstração no seed.** A senha do usuário de exemplo tem default no código
   (`demo1234`, sobrescrevível por `SEED_USER_PASSWORD`); o seed não roda quando
   `APP_ENV=production`.
