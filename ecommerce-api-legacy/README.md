# ecommerce-api-legacy

API de LMS (plataforma de cursos) com fluxo de checkout, construída em **Node.js + Express + SQLite**.

## O que faz

Gerencia cursos, matrículas e pagamentos. O fluxo principal é o checkout: um usuário pode se matricular em um curso e pagar com cartão em uma única requisição.

### Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/checkout` | Matricula um usuário em um curso e processa o pagamento |
| `GET` | `/api/admin/financial-report` | Relatório financeiro agrupado por curso (receita + alunos) |
| `DELETE` | `/api/users/:id` | Remove um usuário e seus dados associados (cascade) |

### Fluxo de Checkout

1. Recebe dados do usuário, curso e cartão
2. Busca o curso (deve estar ativo)
3. Busca o usuário pelo email — cria se não existir (senha com bcrypt)
4. Valida o cartão (prefixo "4" = aprovado)
5. Cria matrícula → registra pagamento → gera audit log
6. Retorna o ID da matrícula

### Banco de Dados

SQLite em memória (`:memory:`), inicializado com seed data a cada boot:

| Tabela | Descrição |
|--------|-----------|
| `users` | Usuários (nome, email, senha hasheada) |
| `courses` | Cursos disponíveis (título, preço, ativo) |
| `enrollments` | Matrículas (relação usuário ↔ curso) |
| `payments` | Pagamentos (valor, status: PAID/DENIED) |
| `audit_logs` | Log de ações do sistema |

### Dados de Exemplo (seed)

- **Usuário:** Leonan (`leonan@fullcycle.com.br`, senha: `123`)
- **Cursos:** Clean Architecture (R$ 997), Docker (R$ 497)
- **Matrícula + pagamento** já existentes para o usuário 1 no curso 1

## Como rodar

```bash
npm install
npm start
```

Sobe em `http://localhost:3000`. Exemplos de requisições no arquivo `api.http`.

## Arquitetura

```
src/
  app.js                     # Entry point — sobe Express, init DB, registra rotas
  config/index.js            # Variáveis de ambiente (via dotenv)
  database/
    connection.js            # Factory de conexão SQLite + helpers (run/get/all)
    schema.js                # Criação de tabelas + seed data
  models/                    # Um arquivo por domínio — acesso ao banco
    userModel.js             # CRUD de usuários + hash de senha (bcrypt)
    courseModel.js           # Busca de cursos
    enrollmentModel.js       # Criação/remoção de matrículas
    paymentModel.js          # Criação/remoção de pagamentos
    auditLogModel.js         # Registro de audit logs
    reportModel.js           # Relatório financeiro (JOIN)
  controllers/               # Lógica de negócio — orquestram models/services
    checkoutController.js    # Fluxo completo de checkout
    reportController.js      # Agrupamento do relatório financeiro
    userController.js        # Remoção de usuário com cascade
  routes/                    # Definição de endpoints — extraem params e chamam controllers
    checkoutRoutes.js
    reportRoutes.js
    userRoutes.js
    index.js                 # Agregador de rotas
  services/
    paymentService.js        # Validação de cartão (regra de negócio isolada)
  middlewares/
    errorHandler.js          # Error handling centralizado (AppError)
```

**Direção de dependência:** Routes → Controllers → Models. Nunca o reverso.

## Configuração

Nenhum secret é hardcoded — tudo vem de variáveis de ambiente. Veja `.env.example`:

```env
PORT=3000
DB_PATH=:memory:
PAYMENT_GATEWAY_KEY=
SMTP_USER=
SMTP_PASS=
```

## Erros

Todos os erros seguem formato JSON consistente:

```json
{ "error": { "code": 400, "message": "descrição do problema" } }
```
