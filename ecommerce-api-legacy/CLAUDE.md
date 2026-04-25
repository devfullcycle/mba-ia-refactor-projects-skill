# ecommerce-api-legacy — LMS API com Checkout

Node.js/Express API de LMS (cursos, matrículas, pagamentos, checkout).

## Stack
- Node.js + Express 4.18 + sqlite3 5.1
- SQLite em memória (`:memory:` — dados perdidos ao reiniciar)
- Sem ORM — callbacks diretas do sqlite3

## Como rodar
```bash
npm install
npm start
# Roda em http://localhost:3000
```

## Estrutura atual
```
src/app.js          # Entry point, cria Express + AppManager
src/AppManager.js   # God Class: init DB, define routes, business logic
src/utils.js        # Config hardcoded, cache global, badCrypto()
package.json        # express, sqlite3
api.http            # Exemplos de requisições (VS Code REST Client)
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/checkout` | Checkout: cria usuário se não existe, matricula, processa pagamento |
| GET | `/api/admin/financial-report` | Relatório financeiro por curso (receita + alunos) |
| DELETE | `/api/users/:id` | Deleta usuário (sem cascade) |

## Tabelas SQLite (in-memory)
- `users` (id, name, email, pass)
- `courses` (id, title, price, active)
- `enrollments` (id, user_id, course_id)
- `payments` (id, enrollment_id, amount, status)
- `audit_logs` (id, action, created_at)

## Fluxo principal — Checkout
1. Recebe `usr`, `eml`, `pwd`, `c_id`, `card` no body
2. Busca curso por ID
3. Busca usuário por email; se não existe, cria com `badCrypto(pwd)`
4. Valida cartão: começa com "4" = aprovado, senão recusado
5. Cria matrícula → cria pagamento → cria audit log → retorna sucesso

## Problemas conhecidos (análise manual)
- Hardcoded: senha DB, payment gateway key, credenciais SMTP
- Weak cryptography: `badCrypto()` é loop de base64 sem segurança
- Log de número de cartão de crédito no console
- God Class: AppManager faz tudo (DB init + routes + business logic)
- Callback hell: 4-5 níveis de nesting no checkout
- N+1 queries no financial-report (curso → matrículas → user + payment)
- DELETE de usuário sem cascade (matrículas e pagamentos ficam órfãos)
- Estado global mutável (`globalCache`, `totalRevenue`)
- Variáveis com nomes obscuros (`u`, `e`, `p`, `cid`, `cc`)
