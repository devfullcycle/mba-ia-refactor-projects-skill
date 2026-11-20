# Validação pós-refatoração — Projeto 2 (ecommerce-api-legacy)

Gerado com um smoke test HTTP independente (fora da skill): a mesma lista de requisições foi enviada à aplicação **original** (baseline) e à **refatorada**, sobre um banco recém-criado.

## Boot da aplicação refatorada

```
$ ADMIN_TOKEN=*** PAYMENT_GATEWAY_KEY=*** npm start
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js
2026-11-20T02:00:21.085Z INFO LMS API rodando na porta 3000
2026-11-20T02:00:21.268Z INFO Processando pagamento de 497 no cartão ****4444
2026-11-20T02:00:21.303Z INFO Checkout concluído: curso=2 usuario=2 matricula=2
2026-11-20T02:00:21.307Z INFO Processando pagamento de 497 no cartão ****4444
2026-11-20T02:00:21.307Z INFO Checkout concluído: curso=2 usuario=1 matricula=3
2026-11-20T02:00:21.310Z INFO Processando pagamento de 997 no cartão ****4444
2026-11-20T02:00:21.320Z INFO Usuário 1 removido com matrículas e pagamentos
```

## Comparação antes × depois

| # | Request | Antes | Depois | Resultado |
|---|---|---|---|---|
| 1 | `GET /api/admin/financial-report` — report inicial | 200 | 200 | ✅ igual |
| 2 | `GET /api/admin/financial-report` — report sem token | — | 403 | 🆕 relatório exige `X-Admin-Token` |
| 3 | `POST /api/checkout` — checkout sucesso (novo usuario) | 200 | 200 | ✅ igual |
| 4 | `POST /api/checkout` — checkout usuario existente | 200 | 200 | ✅ igual |
| 5 | `POST /api/checkout` — checkout pagamento recusado | 400 | 400 | ✅ igual |
| 6 | `POST /api/checkout` — checkout curso inexistente | 404 | 404 | ✅ igual |
| 7 | `POST /api/checkout` — checkout bad request | 400 | 400 | ✅ igual |
| 8 | `GET /api/admin/financial-report` — report apos checkouts | 200 | 200 | ✅ igual |
| 9 | `DELETE /api/users/1` — deletar usuario | 200 | 200 | ✅ igual (mensagem sem o aviso de dados sujos) |
| 10 | `GET /api/admin/financial-report` — report apos delete | 200 | 200 | ✅ igual (delete em cascata: aluno órfão (`Unknown`) não aparece mais) |
| 11 | `GET /nao-existe` — rota inexistente | 404 | 404 | ✅ igual |
| 12 | `POST /api/checkout` — checkout card numerico (crash antes) | — | 400 | 🆕 antes derrubava o servidor (TypeError) |
| 13 | `DELETE /api/users/999` — delete user inexistente | — | 404 | 🆕 404 em vez de 200 |

**10 iguais ao baseline · 0 mudanças intencionais · 3 verificações novas · 0 erros 5xx**
