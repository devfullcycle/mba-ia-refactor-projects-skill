================================
VALIDATION EVIDENCE — ecommerce-api-legacy
================================
Date:  2026-07-13
Stack: JavaScript (Node.js 20) + Express 4
Port:  3000

## Boot
$ npm install
$ ADMIN_TOKEN=dev-admin-token node src/app.js
[log] LMS API rodando na porta 3000...
Boot: ✓ OK  (sem stack trace; schema + seed carregados no boot)

## Endpoints
| Método | Path                          | Payload                                                        | Status | Esperado | OK |
|--------|-------------------------------|----------------------------------------------------------------|--------|----------|----|
| POST   | /api/checkout                 | {usr,eml,pwd,c_id:2,card:"4111..."} (aprovado)                 | 200    | 200      | ✓  |
| POST   | /api/checkout                 | {usr,eml,pwd,c_id:1,card:"5111..."} (recusado)                | 400    | 400      | ✓  |
| POST   | /api/checkout                 | {} (campos obrigatórios faltando)                              | 400    | 400      | ✓  |
| GET    | /api/admin/financial-report   | — (sem x-admin-token)                                          | 401    | 401      | ✓  |
| GET    | /api/admin/financial-report   | header x-admin-token válido                                    | 200    | 200      | ✓  |
| DELETE | /api/users/1                  | — (sem x-admin-token)                                          | 401    | 401      | ✓  |
| DELETE | /api/users/1                  | header x-admin-token válido                                    | 200    | 200      | ✓  |
| GET    | /api/admin/financial-report   | header válido (pós-delete, checa integridade)                 | 200    | 200      | ✓  |

## Amostras de resposta (trechos reais)
- POST /api/checkout (aprovado) → 200 : {"msg":"Sucesso","enrollment_id":2}
- POST /api/checkout (recusado) → 400 : Pagamento recusado
- POST /api/checkout (vazio)    → 400 : Bad Request
- GET  /api/admin/financial-report (sem token) → 401 : Unauthorized
- GET  /api/admin/financial-report (com token) → 200 :
    [{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},
     {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
- DELETE /api/users/1 (sem token) → 401 : Unauthorized
- DELETE /api/users/1 (com token) → 200 : Usuário e dados relacionados (matrículas e pagamentos) removidos.
- GET  /api/admin/financial-report (pós-delete) → 200 :
    [{"course":"Clean Architecture","revenue":0,"students":[]},
     {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
  ↑ Prova da correção AP-12: após remover o usuário 1, a matrícula/pagamento dele saíram junto
    (revenue 0, students []). Nenhum dado órfão — o bug original ("ficaram sujos no banco") foi corrigido.

## Notas
- Formato de resposta do relatório preservado: [{course, revenue, students:[{student, paid}]}].
- Rotas admin agora exigem header x-admin-token (correção AP-13); o 401 sem token é o
  comportamento esperado e conta como OK ao comparar com a coluna "Esperado".
- Node 12 (default do shell) tem npm quebrado; validação feita com Node 20 via nvm.

================================
RESULT: PASS (8/8 endpoints)
================================
