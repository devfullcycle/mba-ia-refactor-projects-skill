# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, refatorada para o padrão MVC.

## Como rodar

Requer Node.js >= 20.12 (usa `process.loadEnvFile` e `crypto.scrypt` nativos, sem dependências extras).

```bash
npm install
cp .env.example .env   # defina ADMIN_TOKEN para habilitar as rotas administrativas
npm start
```

A aplicação sobe em `http://localhost:3000`. Por padrão o banco SQLite é em memória (`DB_PATH=:memory:`) e é populado com dados de exemplo no boot (desative com `SEED_DB=false`).

Exemplos de requisições estão em `api.http`.

## Estrutura

```text
src/
├── app.js              # entrypoint: createApp() + start() (conexão, seed e listen)
├── config/             # variáveis de ambiente, logger, conexão/schema SQLite (Promise + transações), seed
├── models/             # acesso a dados (users, courses, enrollments, payments, audit_logs)
├── controllers/        # regras de negócio: checkout, relatório financeiro, exclusão de usuário
├── services/           # gateway de pagamento (simulado)
├── routes/             # mapeamento HTTP -> controllers
├── middlewares/        # token administrativo e tratamento global de erros
└── utils/              # erros de domínio, constantes, hash de senha, asyncHandler
```

## Endpoints

| Método | Rota | Proteção | Descrição |
|---|---|---|---|
| `POST` | `/api/checkout` | — | Body `{ usr, eml, pwd, c_id, card }` → `200 { msg, enrollment_id }` |
| `GET` | `/api/admin/financial-report` | `X-Admin-Token` | `[{ course, revenue, students: [{ student, paid }] }]` |
| `DELETE` | `/api/users/:id` | `X-Admin-Token` | Remove o usuário e, em cascata, matrículas e pagamentos |

Erros continuam em texto puro, como no legado (`400 Bad Request`, `400 Pagamento recusado`, `404 Curso não encontrado`).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Arquivo SQLite |
| `SEED_DB` / `SEED_USER_PASSWORD` | `true` / aleatória | Dados de exemplo |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway (obrigatória em `NODE_ENV=production`) |
| `ADMIN_TOKEN` | vazio | Habilita as rotas administrativas (header `X-Admin-Token`) |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn` ou `error` |

## Mudanças de comportamento em relação ao legado

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token` (`403` se `ADMIN_TOKEN` não estiver configurado, `401` se o token for inválido).
- No checkout de um usuário novo, `pwd` é obrigatório (antes ele recebia a senha padrão `123456`). As senhas são gravadas com `scrypt` e salt.
- Um pagamento recusado não cria mais o usuário no banco. Matrícula, pagamento e auditoria são gravados na mesma transação.
- `DELETE /api/users/:id` responde `404` quando o usuário não existe e remove matrículas e pagamentos em cascata.
- O relatório financeiro sai ordenado por curso e matrícula (antes a ordem dependia de quando cada callback terminava).
