# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch` — **refatorada para MVC** pela skill (`.claude/skills/refactor-arch`).

## Como rodar

```bash
npm install
ADMIN_TOKEN=troque-este-token npm start
```

A aplicação sobe em `http://localhost:3000` (`PORT` configurável). O banco SQLite é em memória (`DATABASE_FILE`) e carrega seeds automaticamente no boot. Variáveis disponíveis em `.env.example`.

Exemplos de requisições estão em `api.http`. Os endpoints administrativos (`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header `X-Admin-Token` igual ao `ADMIN_TOKEN`; sem `ADMIN_TOKEN` eles ficam desabilitados (403).

## Estrutura

```
src/
├── app.js                  # composition root (createApp + listen)
├── config/index.js         # configuração via process.env
├── database/               # wrapper async do sqlite3 com transações + schema/seed
├── models/                 # userModel, courseModel (relatório com JOIN), enrollmentModel
├── services/               # pagamento (simulado), hash de senha (scrypt), cache
├── controllers/            # checkout, relatório, usuários
├── views/routes.js         # rotas Express → controllers
├── middlewares/            # asyncHandler, requireAdmin, errorHandler
└── utils/                  # erros de domínio, logger
```
