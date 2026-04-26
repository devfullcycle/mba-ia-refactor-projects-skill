# ecommerce-api-legacy — LMS API com Checkout

Node.js/Express API de LMS (cursos, matrículas, pagamentos, checkout) refatorada para arquitetura MVC.

## Stack
- Node.js + Express 4.18 + sqlite3 5.1
- bcryptjs para hashing de senhas
- dotenv para configuração via variáveis de ambiente
- SQLite em memória (`:memory:` — dados perdidos ao reiniciar)

## Como rodar
```bash
npm install
npm start
# Roda em http://localhost:3000
```

## Estrutura MVC
```
src/
  app.js                          # Entry point (composition root)
  config/
    index.js                      # Config from env vars
  database/
    connection.js                 # SQLite connection factory + query helpers (promisified)
    schema.js                     # Schema creation + seeding
  models/
    auditLogModel.js              # Audit log data access
    courseModel.js                # Course data access
    enrollmentModel.js            # Enrollment data access
    paymentModel.js               # Payment data access
    reportModel.js                # Financial report (JOIN query)
    userModel.js                  # User data access + bcrypt hashing
  controllers/
    checkoutController.js         # Checkout business logic
    reportController.js           # Report aggregation logic
    userController.js             # User deletion + cascade
  routes/
    checkoutRoutes.js             # POST /api/checkout
    reportRoutes.js               # GET /api/admin/financial-report
    userRoutes.js                 # DELETE /api/users/:id
    index.js                      # Route aggregator
  services/
    paymentService.js             # Payment processing (card validation)
  middlewares/
    errorHandler.js               # Centralized error handling (AppError class)
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/checkout` | Checkout: cria usuário se não existe, matricula, processa pagamento |
| GET | `/api/admin/financial-report` | Relatório financeiro por curso (receita + alunos) |
| DELETE | `/api/users/:id` | Deleta usuário com cascade (enrollments + payments) |

## Request body — Checkout
```json
{
  "userName": "Nome",
  "email": "email@example.com",
  "password": "senha",
  "courseId": 1,
  "cardNumber": "4111222233334444"
}
```

## Tabelas SQLite (in-memory)
- `users` (id, name, email, pass)
- `courses` (id, title, price, active)
- `enrollments` (id, user_id, course_id)
- `payments` (id, enrollment_id, amount, status)
- `audit_logs` (id, action, created_at)

## Variáveis de ambiente
Ver `.env.example` para todas as variáveis necessárias. Nenhum secret é hardcoded no código.

## Regras de erro
Todos os erros passam pelo middleware centralizado (`errorHandler.js`) e retornam formato JSON consistente:
```json
{ "error": { "code": 400, "message": "descrição" } }
```
