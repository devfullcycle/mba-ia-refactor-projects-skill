# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express — refatorada para o padrão MVC pela skill `refactor-arch`.

## Estrutura

```
src/
├── app.js                     # composition root
├── config/settings.js         # variáveis de ambiente via dotenv
├── database/index.js          # singleton SQLite + wrappers Promise
├── models/                    # acesso ao banco por domínio
│   ├── UserModel.js
│   ├── CourseModel.js
│   ├── EnrollmentModel.js
│   └── PaymentModel.js
├── services/
│   └── CheckoutService.js     # orquestra checkout com transação DB
├── controllers/               # validação de entrada + fluxo HTTP
│   ├── CheckoutController.js
│   ├── ReportController.js
│   └── UserController.js
├── routes/                    # só definição de rotas
│   ├── checkoutRoutes.js
│   ├── reportRoutes.js
│   └── userRoutes.js
└── middlewares/
    ├── auth.js                # guarda x-admin-api-key
    └── errorHandler.js
```

## Como rodar

```bash
cp .env.example .env   # preencha PAYMENT_GATEWAY_KEY e ADMIN_API_KEY
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e carrega seeds automaticamente no boot.

## Endpoints

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/api/checkout` | — | Cria usuário (se não existir), processa pagamento e enrola no curso |
| `GET` | `/api/admin/financial-report` | `x-admin-api-key` | Relatório de receita e alunos por curso |
| `DELETE` | `/api/users/:id` | `x-admin-api-key` | Remove usuário e todos os registros associados (cascade) |

### Autenticação nas rotas admin

Passe o header `x-admin-api-key` com o valor definido em `ADMIN_API_KEY` no `.env`:

```bash
curl http://localhost:3000/api/admin/financial-report \
  -H "x-admin-api-key: dev-admin-key-not-for-production"
```

### Exemplo de checkout

```bash
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"username":"Ana","email":"ana@test.com","courseId":1,"cardNumber":"4111111111111111"}'
```

Exemplos adicionais estão em `api.http`.
