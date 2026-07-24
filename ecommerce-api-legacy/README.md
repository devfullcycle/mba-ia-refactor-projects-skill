# ecommerce-api-legacy

LMS API em Node.js/Express — checkout de curso com matrícula, pagamento, auditoria e
relatório financeiro.

Projeto refatorado para MVC pela skill [`refactor-arch`](.claude/skills/refactor-arch/).
Auditoria: [`reports/audit-project-2.md`](../reports/audit-project-2.md) ·
Validação: [`reports/validation-project-2.md`](../reports/validation-project-2.md).

## Como rodar

```bash
npm install
ADMIN_API_KEY=uma-chave-local npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória e carrega os dados de
demonstração a cada boot.

Configuração por variáveis de ambiente — ver [`.env.example`](.env.example).
**Sem `ADMIN_API_KEY` definida, as rotas administrativas respondem 401** (negar por default);
`PAYMENT_GATEWAY_KEY` passa a ser obrigatória quando `APP_ENV=production`.

## Estrutura

```
src/
├── config/index.js                             # process.env → configuração, obrigatórios validados
├── database/{connection,schema,seed}.js        # driver promisificado + transação
├── models/*.repository.js                      # user, course, enrollment, payment, audit
├── services/{checkout,report}.service.js, payment-gateway.js
├── controllers/{checkout,report,user}.controller.js
├── routes/index.js                             # só mapeamento
├── middlewares/{auth,errorHandler}.js
├── validators/checkout.validator.js
├── utils/{logger,errors,password,memory-cache}.js
└── app.js                                      # composition root (createApp, sem listen)
server.js                                       # entry point
```

## Endpoints

| Método | Rota | Autenticação |
|---|---|---|
| POST | `/api/checkout` | pública |
| GET | `/api/admin/financial-report` | header `x-api-key` |
| DELETE | `/api/users/:id` | header `x-api-key` |

O contrato do checkout foi preservado (`usr`, `eml`, `pwd`, `c_id`, `card`); os nomes de
domínio (`name`, `email`, `password`, `courseId`) são aceitos como alias. Exemplos em
[`api.http`](api.http).

## Validação

```bash
../scripts/smoke-project-2.sh /tmp/p2     # 8 chamadas nos 3 endpoints
```

As duas rotas administrativas retornam 401 nessa bateria — comportamento esperado sem
credencial. Para exercitá-las:

```bash
curl -H "x-api-key: uma-chave-local" http://localhost:3000/api/admin/financial-report
```
