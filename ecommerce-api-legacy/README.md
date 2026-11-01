# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC + Services + Repositories.

## Como rodar

```bash
npm install
cp .env.example .env   # ajuste os valores
npm start
```

A aplicação sobe em `http://localhost:3000` por padrão. O banco SQLite é em memória (`:memory:`) e já carrega seeds automaticamente no boot. O `dotenv` carrega automaticamente o arquivo `.env` (variáveis já definidas no ambiente têm precedência).

## Variáveis de ambiente

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `PORT` | não | `3000` | Porta HTTP |
| `DATABASE_PATH` | não | `:memory:` | Caminho do arquivo SQLite ou `:memory:` |
| `ADMIN_TOKEN` | em produção | — | Token Bearer para rotas administrativas |
| `PAYMENT_GATEWAY_KEY` | em produção | — | Chave do gateway (não é logada) |
| `LOG_LEVEL` | não | `info` | `error`, `warn`, `info` ou `debug` |

Segredos não possuem default em produção: a aplicação falha no boot se `ADMIN_TOKEN` ou `PAYMENT_GATEWAY_KEY` estiverem ausentes com `NODE_ENV=production`.

## Autenticação

`GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem:

```http
Authorization: Bearer <ADMIN_TOKEN>
```

Sem `ADMIN_TOKEN` configurado, essas rotas respondem `503` (fail closed). Com token inválido, `401`.

`POST /api/checkout` é público para cadastro de um novo usuário (a conta é criada com o `pwd` enviado). Se o e-mail já pertence a uma conta, o checkout exige a senha do titular em `pwd`; sem ela ou com senha incorreta, responde `401 Credenciais inválidas`. O dono da matrícula nunca é escolhido por um id enviado no body.

## Endpoints

| Método | Rota | Autenticação | Resposta |
|---|---|---|---|
| `POST` | `/api/checkout` | pública para novo usuário; senha do titular para conta existente | `200 {"msg":"Sucesso","enrollment_id":N}`; `400 Bad Request`; `400 Pagamento recusado`; `401 Credenciais inválidas`; `404 Curso não encontrado` |
| `GET` | `/api/admin/financial-report` | admin | `200 [{course, revenue, students:[{student, paid}]}]` |
| `DELETE` | `/api/users/:id` | admin | `200 Usuário deletado com sucesso.`; `404 Usuário não encontrado` |

Exemplos de requisições estão em `api.http`.

## Testes

```bash
npm test
```

A suíte usa o test runner nativo do Node (`node:test`), sobe a aplicação em porta efêmera e cobre as três rotas, validação, autenticação, agregação do relatório e remoção em cascata.

## Estrutura

```
src/
├── app.js                 # composição da aplicação e boot
├── container.js           # injeção de dependências
├── config/                # configuração via ambiente
├── database/              # conexão, migrations versionadas + seeds
├── models/                # entidades e invariantes
├── repositories/          # acesso a dados (queries parametrizadas)
├── services/              # regras de negócio
├── controllers/           # orquestração HTTP
├── routes/                # registro de rotas por recurso
├── middleware/            # auth, erros, 404
├── validators/            # validação de entrada
└── utils/                 # hash de senha e logger
```

## Notas de migração

- Senhas agora usam `scrypt` com salt (formato `scrypt$salt$hash`). O seed do usuário `Leonan` recebe uma senha aleatória, gravada apenas como hash — não há literal de senha no código.
- O `DELETE /api/users/:id` remove pagamentos e matrículas na mesma transação, em vez de deixar registros órfãos.
- Erros internos retornam `500 Internal Server Error` genérico, sem vazar detalhes do banco.
- Rotas administrativas passaram a exigir autenticação; ajuste clientes que as chamavam anonimamente.
- Checkout em nome de uma conta existente passou a exigir a senha do titular (`401` sem ela ou com senha incorreta); antes o e-mail do body era aceito sem prova de posse (SEC-04/IDOR).
- Usuário novo só é persistido depois da aprovação do pagamento, dentro da mesma transação da matrícula/pagamento/auditoria.
