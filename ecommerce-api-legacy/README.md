# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada em camadas
(config, domain, application, adapters/http, infrastructure) a partir do
relatório [`reports/audit-project-2.md`](../reports/audit-project-2.md).

## Como rodar

```bash
npm install
cp .env.example .env   # preencha com valores próprios; nenhum é um segredo real
node --env-file=.env src/app.js
# ou: npm start (com as variáveis já exportadas no shell)
```

Variáveis de ambiente obrigatórias (o boot falha com mensagem clara se faltar alguma):

| Variável | Uso |
| --- | --- |
| `PAYMENT_GATEWAY_KEY` | chave do adapter de pagamento (simulação local) |
| `ADMIN_API_KEY` | API key com papel `admin` (relatório financeiro e exclusão de usuário) |
| `USER_API_KEY` | API key com papel `user` (checkout) |
| `USER_EMAIL` | e-mail da identidade vinculada à `USER_API_KEY` |
| `PORT` | porta HTTP (opcional, default `3000`) |

A aplicação sobe em `http://localhost:3000` (ou a porta configurada). O banco
SQLite (`node:sqlite`) é em memória e carrega seeds de demonstração no boot.

## Autenticação

Todas as rotas exigem o header `x-api-key`. No `POST /api/checkout`, a chave
de usuário só pode operar para o `eml` configurado em `USER_EMAIL`; tentativas
de checkout em nome de outro e-mail retornam `403`. A chave administrativa
possui política explícita para checkout de qualquer e-mail. O relatório
financeiro e a exclusão de usuário continuam restritos ao papel `admin`.

## Exclusão de usuário

`DELETE /api/users/:id` segue a política RESTRICT: recusa a exclusão com
`409` quando o usuário possui matrícula ou pagamento vinculado, evitando
registros órfãos. Resposta em JSON (`{ "message": ..., "id": ... }`).

Exemplos de requisições estão em `api.http`.

## Testes

```bash
npm test
```

Cobre hashing de senha (unit), caso de uso de checkout com atomicidade
(unit), exclusão de usuário com integridade referencial (integration) e
contratos HTTP dos três endpoints, incluindo autenticação/autorização e
ausência de PAN nos logs (contract).
