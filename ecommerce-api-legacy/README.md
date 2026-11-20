# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=um-token-forte npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

As variáveis de ambiente estão documentadas em `.env.example`. As rotas administrativas
(`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header
`X-Admin-Token` com o valor de `ADMIN_TOKEN`; sem `ADMIN_TOKEN` definido elas respondem 403.

Exemplos de requisições estão em `api.http`.

## Estrutura (MVC)

```
src/
├── app.js          # composition root + listen
├── config/         # leitura de variáveis de ambiente
├── models/         # conexão SQLite, schema, seed e repositórios
├── controllers/    # regras de negócio, validação e erros de domínio
├── routes/         # rotas Express (camada HTTP)
├── views/          # mapeamento request/response (contrato público)
├── services/       # gateway de pagamento, hash de senha, logger
└── middlewares/    # tratamento de erros, auth admin, asyncHandler
```
