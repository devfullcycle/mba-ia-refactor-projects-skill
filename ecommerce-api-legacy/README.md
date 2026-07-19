# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Configuração e segredos vêm do ambiente (veja `.env.example`). As rotas administrativas
(`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header
`x-admin-token` igual ao `ADMIN_TOKEN` (default de desenvolvimento: `dev-admin-token`).

Exemplos de requisições estão em `api.http`.
