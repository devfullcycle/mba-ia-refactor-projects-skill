# Audit Report — Project 2: ecommerce-api-legacy

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API com fluxo de checkout (cursos, matrículas, pagamentos)
Architecture:  Monolítica — toda lógica em uma classe AppManager, sem separação de camadas
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials and API Keys
File: src/utils.js:1-7
Description: Credenciais de produção hardcoded no código fonte: `dbUser: "admin_master"`, `dbPassword: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"`. Todas expostas diretamente no arquivo.
Impact: Qualquer pessoa com acesso ao repositório tem credenciais de banco de dados, gateway de pagamento e email. Comprometimento total do sistema.
Recommendation: Mover todas as credenciais para variáveis de ambiente usando `dotenv`. Criar arquivo `.env` (adicionado ao `.gitignore`).

### [CRITICAL] Insecure Password Hashing
File: src/utils.js:17-23
Description: Função `badCrypto()` usa `Buffer.from(pwd).toString('base64')` repetido 10.000 vezes e retorna apenas 10 caracteres. Base64 é encoding reversível, não hashing criptográfico.
Impact: Todas as senhas podem ser facilmente revertidas. Base64 não oferece proteção real.
Recommendation: Substituir por `bcrypt.hash(password, 10)` para hashing e `bcrypt.compare()` para verificação.

### [CRITICAL] Secrets Logged to Console
File: src/AppManager.js:45
Description: Chave do gateway de pagamento é logada no console: `console.log('Processando cartão ... chave ${config.paymentGatewayKey}')`. Número do cartão também é parcialmente logado.
Impact: Secrets e dados de cartão de crédito expostos em logs de produção. Violação de PCI-DSS.
Recommendation: Nunca logar secrets ou dados de cartão. Usar logging estruturado sem dados sensíveis.

### [HIGH] Callback Hell / Pyramid of Doom
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: Callbacks aninhados em 6-7 níveis no endpoint POST `/api/checkout` (linhas 37-76) e 4-5 níveis no GET `/api/admin/financial-report` (linhas 83-127). Uso de `const self = this` para manter contexto (linha 26).
Impact: Código extremamente difícil de ler, manter e depurar. Tratamento de erros inconsistente. Risco de race conditions.
Recommendation: Refatorar para async/await. Promisificar operações do banco de dados com wrappers `dbGet()`, `dbRun()`.

### [HIGH] Missing Authentication/Authorization
File: src/AppManager.js:80, src/AppManager.js:131
Description: Endpoint admin `/api/admin/financial-report` (linha 80) e DELETE `/api/users/:id` (linha 131) são publicamente acessíveis sem qualquer autenticação.
Impact: Qualquer pessoa pode acessar dados financeiros sensíveis e deletar usuários do sistema.
Recommendation: Implementar middleware de autenticação JWT. Adicionar verificação de role para endpoints admin.

### [HIGH] Data Integrity Violation on Delete
File: src/AppManager.js:131-137
Description: DELETE `/api/users/:id` remove o usuário mas deixa matrículas e pagamentos órfãos no banco. Comentário no código confirma: "matrículas e pagamentos ficaram sujos".
Impact: Dados órfãos se acumulam. Relatórios financeiros ficam inconsistentes. Integridade referencial comprometida.
Recommendation: Implementar cascade delete ou soft delete. Adicionar FOREIGN KEY constraints com ON DELETE CASCADE.

### [MEDIUM] N+1 Query Problem
File: src/AppManager.js:80-129
Description: Relatório financeiro executa queries aninhadas: 1 query para cursos, para cada curso 1 query para matrículas, para cada matrícula 1 query para usuário e 1 para pagamento. Até 12+ queries para 2 cursos.
Impact: Performance degrada exponencialmente com volume de dados.
Recommendation: Usar uma única query JOIN: `SELECT c.*, e.*, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON ...`

### [MEDIUM] Global Mutable State
File: src/utils.js:9-10
Description: `globalCache = {}` e `totalRevenue = 0` são variáveis globais mutáveis. Cache sem expiração, sem limite de tamanho, sem limpeza. `totalRevenue` exportado mas nunca utilizado.
Impact: Memory leak potencial — cache cresce indefinidamente. Estado global compartilhado entre requests.
Recommendation: Usar solução de cache adequada (Redis, node-cache com TTL). Remover variáveis não utilizadas.

### [MEDIUM] No Input Validation
File: src/AppManager.js:29-33
Description: Dados do request usados diretamente sem validação: `const u = req.body.usr`, `const cc = req.body.card`. Nomes de variáveis abreviados (`u`, `e`, `p`, `cid`, `cc`) dificultam compreensão. Nenhuma validação de formato de email, força de senha, formato de cartão.
Impact: Dados inválidos entram no sistema. Aplicação pode crashar com inputs inesperados.
Recommendation: Implementar validação com biblioteca (Joi, Zod). Usar nomes descritivos: `username`, `email`, `password`, `courseId`, `cardNumber`.

### [MEDIUM] Trivial Payment Validation
File: src/AppManager.js:45-46
Description: Lógica de pagamento baseada apenas no prefixo do cartão: `card.startsWith("4")` = PAID, qualquer outro = DENIED. Sem integração real com gateway de pagamento. Senha padrão `"123456"` quando não fornecida (linha 68).
Impact: Sistema de pagamento completamente inseguro. Qualquer número começando com "4" é aceito.
Recommendation: Integrar com gateway de pagamento real (Stripe, PagSeguro). Implementar validação adequada de cartão.

### [MEDIUM] Deprecated API Usage
File: src/AppManager.js (callback-based sqlite3)
Description: Uso de API callback-based do sqlite3 ao invés de Promises/async-await moderno. Padrões como `db.get(sql, params, callback)` e `db.run(sql, params, callback)` são considerados legado.
Impact: Código difícil de manter. Tratamento de erros propenso a falhas. Não aproveita recursos modernos do Node.js.
Recommendation: Usar wrappers Promise ou migrar para `better-sqlite3` que suporta API síncrona. Refatorar para async/await.

### [LOW] Inconsistent Response Format
File: src/AppManager.js:60, 87, 135
Description: POST /checkout retorna JSON `{ msg, enrollment_id }`. GET /admin/financial-report retorna array JSON. DELETE /users retorna texto plano. Sem padrão de resposta consistente.
Impact: Clientes da API precisam tratar diferentes formatos de resposta. Dificulta integração.
Recommendation: Padronizar respostas: `{ success: true, data: {...} }` para sucesso, `{ success: false, error: "..." }` para erro.

### [LOW] Magic Numbers and Poor Naming
File: src/AppManager.js:29-33, src/AppManager.js:46, src/AppManager.js:68
Description: Variáveis com nomes de uma letra: `u`, `e`, `p`, `cid`, `cc`. Validação de cartão com magic string `"4"`. Senha padrão `"123456"` hardcoded. Porta 3000 hardcoded em utils.js:6.
Impact: Código ilegível. Difícil para novos desenvolvedores entenderem a lógica.
Recommendation: Usar nomes descritivos. Definir constantes em módulo de configuração.

================================
Total: 12 findings
================================
```
