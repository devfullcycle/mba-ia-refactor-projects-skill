# 📑 Relatório de Auditoria Arquitetural — `ecommerce-api-legacy`

**Data da Auditoria:** `2026-11-05` (revalidado; auditoria original em `2026-10-30`)  
**Stack Detectada:** `JavaScript (Node.js)` / `Express 4.18`  
**Domínio da Aplicação:** `LMS / venda de cursos online (cursos, matrículas, pagamentos, usuários)`  

---

## 📊 1. Resumo Executivo por Severidade

| Severidade | Quantidade Identificada |
|---|---|
| 🚨 **CRITICAL** | `3` |
| ⚠️ **HIGH** | `4` |
| ⚡ **MEDIUM** | `5` |
| 🔵 **LOW** | `3` |
| **TOTAL** | **`15`** |

> **APIs Deprecated:** nenhuma das APIs listadas no catálogo foi encontrada — o projeto já usa `express.json()` nativo (sem `body-parser`) e não usa `res.sendfile()`.
>
> **SQL Injection:** não encontrado — todas as queries com entrada do usuário usam placeholders `?` do driver `sqlite3`.

---

## 🔍 2. Detalhamento dos Achados

### Achado #1: Hardcoded Secrets
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `src/utils.js (Linhas 1 a 7)`, `src/AppManager.js (Linha 18)`
- **Descrição do Problema:** Usuário/senha do banco (`admin_master` / `senha_super_secreta_prod_123`), chave **live** do gateway de pagamento (`pk_live_...`) e usuário SMTP estão em texto plano no código-fonte e versionados. O seed cria um usuário com senha `'123'` sem hash.
- **Recomendação de Refatoração:** Criar `src/config/config.js` lendo `process.env` (com `dotenv`), adicionar `.env.example` e falhar na inicialização se segredos obrigatórios estiverem ausentes.

### Achado #2: Vazamento de dados sensíveis em log (número de cartão + chave do gateway)
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `src/AppManager.js (Linha 45)`
- **Descrição do Problema:** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave do gateway nos logs a cada checkout — violação direta de PCI-DSS.
- **Recomendação de Refatoração:** Remover o log; isolar o pagamento em `services/paymentService.js` que nunca loga PAN/chaves (no máximo os 4 últimos dígitos mascarados).

### Achado #3: God File / God Class
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 4 a 139)`, `src/utils.js (Linhas 1 a 25)`
- **Descrição do Problema:** A classe `AppManager` cria a conexão, define o schema, faz seed, registra todas as rotas, processa pagamento, cria usuários, matricula, audita e gera relatório financeiro. `utils.js` mistura configuração, cache global, log e "criptografia".
- **Recomendação de Refatoração:** Decompor em `config/database.js`, `models/` (User, Course, Enrollment, Payment, AuditLog), `controllers/` (checkout, relatório, usuários), `routes/` e `middlewares/`.

### Achado #4: Callback Hell Assíncrono
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 37 a 77 — 6 níveis; Linhas 83 a 128 — 5 níveis)`
- **Descrição do Problema:** O checkout aninha `db.get → db.get → db.run → db.run → db.run` e o relatório aninha `db.all → forEach → db.all → forEach → db.get → db.get`, com contadores manuais (`coursesPending`, `enrPending`) para saber quando responder. Difícil de ler, testar e tratar erros.
- **Recomendação de Refatoração:** Criar wrapper promisificado do sqlite3 (`run/get/all` retornando `Promise`) em `config/database.js` e reescrever controllers com `async/await` e `try/catch`.

### Achado #5: Bypass de Camadas / Regras em Rotas
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 28 a 137)`
- **Descrição do Problema:** Os handlers HTTP executam SQL diretamente e contêm regras de domínio: aprovação de pagamento (`cc.startsWith("4")`, L46), criação implícita de usuário com senha padrão, matrícula, auditoria e cálculo de receita.
- **Recomendação de Refatoração:** Rotas apenas delegam para `CheckoutController`, `ReportController`, `UserController`; o acesso a dados fica nos Models; o pagamento vai para um serviço dedicado.

### Achado #6: Hashing de senha inseguro (criptografia caseira) e senha padrão
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `src/utils.js (Linhas 17 a 23)`, `src/AppManager.js (Linha 68)`
- **Descrição do Problema:** `badCrypto` apenas repete os 2 primeiros caracteres do Base64 da senha e trunca em 10 — é reversível, sem salt e gera colisões massivas (todas as senhas com o mesmo prefixo têm o mesmo "hash"). Se a senha não for enviada, o usuário é criado com `"123456"`.
- **Recomendação de Refatoração:** Usar `bcrypt` / `crypto.scrypt` com salt; tornar a senha obrigatória e validada no Controller.

### Achado #7: Endpoints administrativos e destrutivos sem autenticação
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 80 e 131)`
- **Descrição do Problema:** `GET /api/admin/financial-report` (dados financeiros e nomes de alunos) e `DELETE /api/users/:id` são públicos.
- **Recomendação de Refatoração:** Middleware `middlewares/auth.js` exigindo autenticação e papel `admin` nessas rotas.

### Achado #8: Queries N+1 no Banco
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 83 a 128)`
- **Descrição do Problema:** Para cada curso, 1 query de matrículas; para cada matrícula, 1 query de usuário + 1 de pagamento → `1 + C + 2·E` queries.
- **Recomendação de Refatoração:** Uma única query com `LEFT JOIN enrollments/users/payments` e agregação em memória (ou `SUM(CASE ...) GROUP BY course_id`) no `CourseModel`.

### Achado #9: Tratamento Inseguro de Exceções / erros ignorados
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 38, 41, 57, 92 a 93, 104, 106, 133 a 135)`
- **Descrição do Problema:** Vários callbacks ignoram `err`: em L92 um erro deixa `enrollments` `undefined` e `enrollments.length` derruba o processo; o `DELETE` responde sucesso mesmo com erro; falha no audit log é ignorada. Respostas são strings soltas (`"Erro DB"`, `"Bad Request"`) em vez de JSON padronizado; erro de banco no curso vira 404.
- **Recomendação de Refatoração:** Middleware global `middlewares/errorHandler.js`, classes de erro de domínio e formato único `{ error: { message } }`; `async/await` com propagação via `next(err)`.

### Achado #10: Falta de transação e integridade referencial (registros órfãos)
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 12 a 16, 50 a 63, 131 a 136)`
- **Descrição do Problema:** O checkout grava usuário, matrícula, pagamento e auditoria em passos independentes; uma falha no meio deixa matrícula sem pagamento. As tabelas não têm `FOREIGN KEY`, e o `DELETE` de usuário deixa matrículas e pagamentos órfãos (a própria resposta admite isso).
- **Recomendação de Refatoração:** Envolver o checkout em `BEGIN/COMMIT/ROLLBACK`; definir FKs com `ON DELETE CASCADE` (e `PRAGMA foreign_keys = ON`) ou soft delete.

### Achado #11: Estado global mutável e código morto
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/utils.js (Linhas 9 a 15, 25)`, `src/AppManager.js (Linhas 2, 7)`
- **Descrição do Problema:** `globalCache` cresce sem limite (vazamento de memória) e é exportado mutável; `totalRevenue` é importado mas nunca usado; `dbUser`/`dbPass`/`smtpUser` não são usados. O banco é `:memory:`, perdendo todos os dados a cada restart.
- **Recomendação de Refatoração:** Remover código morto; se cache for necessário, encapsulá-lo com TTL/limite; caminho do banco configurável via env.

### Achado #12: Duplicação de código
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 95 a 99 vs 117 a 122; 41, 51, 55, 70, 84)`
- **Descrição do Problema:** A lógica de "finalizar curso e responder quando todos terminarem" está repetida em dois pontos; o padrão `if (err) return res.status(500).send(...)` se repete 5 vezes.
- **Recomendação de Refatoração:** Com `async/await` + `Promise.all` e o error handler global, ambas as duplicações desaparecem.

### Achado #13: Logs e Print Statements Dispersos
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/app.js (Linha 13)`, `src/AppManager.js (Linha 45)`, `src/utils.js (Linha 13)`
- **Descrição do Problema:** `console.log` sem nível, formato ou destino configurável.
- **Recomendação de Refatoração:** Logger estruturado (`pino` ou `winston`) configurado em `config/logger.js`.

### Achado #14: Nomenclatura ruim de variáveis
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/AppManager.js (Linhas 29 a 33, 52, 90)`, `src/utils.js (Linha 17)`
- **Descrição do Problema:** Variáveis `u`, `e`, `p`, `cid`, `cc`, `enrId`; contrato de API com campos crípticos (`usr`, `eml`, `pwd`, `c_id`); nomes como `AppManager` e `badCrypto` não expressam responsabilidade.
- **Recomendação de Refatoração:** Nomes de domínio (`name`, `email`, `password`, `courseId`, `cardNumber`) nos controllers; manter mapeamento do contrato legado no Controller enquanto houver clientes antigos.

### Achado #15: Magic Numbers soltos pelo código
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/utils.js (Linhas 6, 19, 22)`, `src/AppManager.js (Linhas 46, 68)`
- **Descrição do Problema:** `10000`, `10`, `3000`, prefixo `"4"` para aprovação de cartão, senha padrão `"123456"` e status `'PAID'`/`'DENIED'` como strings soltas.
- **Recomendação de Refatoração:** Constantes nomeadas (`PAYMENT_STATUS.PAID`, `PORT` via env) e remoção da regra fake de aprovação em favor de um serviço de pagamento.

---

## 🏗️ 3. Plano de Reestruturação para MVC

1. **Camada Model:** `src/models/userModel.js`, `courseModel.js`, `enrollmentModel.js`, `paymentModel.js`, `auditLogModel.js` — acesso a dados via wrapper promisificado, queries com `JOIN` para o relatório financeiro, schema com `FOREIGN KEY ... ON DELETE CASCADE`.
2. **Camada Controller:** `src/controllers/checkoutController.js` (validação de entrada, criação/busca de usuário com `bcrypt`, pagamento via `services/paymentService.js`, matrícula + pagamento + auditoria em transação), `reportController.js` (agregação de receita), `userController.js` (exclusão consistente).
3. **Camada Routes / Views:** `src/routes/checkoutRoutes.js`, `adminRoutes.js` (protegidas por `middlewares/auth.js`), `userRoutes.js` — handlers `async` finos que delegam ao Controller e respondem JSON padronizado.
4. **Configurações:** `src/config/config.js` (variáveis de ambiente via `dotenv`: porta, caminho do banco, chave do gateway), `src/config/database.js` (conexão única, `PRAGMA foreign_keys = ON`, schema/seed separados), `src/middlewares/errorHandler.js` e `src/config/logger.js`; `src/app.js` apenas monta middlewares e rotas.
