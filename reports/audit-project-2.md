# Audit Report — Project 2: ecommerce-api-legacy

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API com fluxo de checkout (cursos, matriculas, pagamentos)
Architecture:  Monolitica — toda logica em uma classe AppManager, sem separacao de camadas
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
Description: Credenciais de producao hardcoded no codigo fonte: `dbUser: "admin_master"`, `dbPassword: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"`. Todas expostas diretamente no arquivo.
Impact: Qualquer pessoa com acesso ao repositorio tem credenciais de banco de dados, gateway de pagamento e email. Comprometimento total do sistema.
Recommendation: Mover todas as credenciais para variaveis de ambiente usando `dotenv`. Criar arquivo `.env` (adicionado ao `.gitignore`).

### [CRITICAL] Insecure Password Hashing
File: src/utils.js:17-23
Description: Funcao `badCrypto()` usa `Buffer.from(pwd).toString('base64')` repetido 10.000 vezes e retorna apenas 10 caracteres. Base64 e encoding reversivel, nao hashing criptografico.
Impact: Todas as senhas podem ser facilmente revertidas. Base64 nao oferece protecao real.
Recommendation: Substituir por `bcrypt.hash(password, 10)` para hashing e `bcrypt.compare()` para verificacao.

### [CRITICAL] Secrets Logged to Console
File: src/AppManager.js:45
Description: Chave do gateway de pagamento e logada no console: `console.log('Processando cartao ... chave ${config.paymentGatewayKey}')`. Numero do cartao tambem e parcialmente logado.
Impact: Secrets e dados de cartao de credito expostos em logs de producao. Violacao de PCI-DSS.
Recommendation: Nunca logar secrets ou dados de cartao. Usar logging estruturado sem dados sensiveis.

### [HIGH] Callback Hell / Pyramid of Doom
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: Callbacks aninhados em 6-7 niveis no endpoint POST `/api/checkout` (linhas 37-76) e 4-5 niveis no GET `/api/admin/financial-report` (linhas 83-127). Uso de `const self = this` para manter contexto (linha 26).
Impact: Codigo extremamente dificil de ler, manter e depurar. Tratamento de erros inconsistente. Risco de race conditions.
Recommendation: Refatorar para async/await. Promisificar operacoes do banco de dados com wrappers `dbGet()`, `dbRun()`.

### [HIGH] Missing Authentication/Authorization
File: src/AppManager.js:80, src/AppManager.js:131
Description: Endpoint admin `/api/admin/financial-report` (linha 80) e DELETE `/api/users/:id` (linha 131) sao publicamente acessiveis sem qualquer autenticacao.
Impact: Qualquer pessoa pode acessar dados financeiros sensiveis e deletar usuarios do sistema.
Recommendation: Implementar middleware de autenticacao JWT. Adicionar verificacao de role para endpoints admin.

### [HIGH] Data Integrity Violation on Delete
File: src/AppManager.js:131-137
Description: DELETE `/api/users/:id` remove o usuario mas deixa matriculas e pagamentos orfaos no banco. Comentario no codigo confirma: "matriculas e pagamentos ficaram sujos".
Impact: Dados orfaos se acumulam. Relatorios financeiros ficam inconsistentes. Integridade referencial comprometida.
Recommendation: Implementar cascade delete ou soft delete. Adicionar FOREIGN KEY constraints com ON DELETE CASCADE.

### [MEDIUM] N+1 Query Problem
File: src/AppManager.js:80-129
Description: Relatorio financeiro executa queries aninhadas: 1 query para cursos, para cada curso 1 query para matriculas, para cada matricula 1 query para usuario e 1 para pagamento. Ate 12+ queries para 2 cursos.
Impact: Performance degrada exponencialmente com volume de dados.
Recommendation: Usar uma unica query JOIN: `SELECT c.*, e.*, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON ...`

### [MEDIUM] Global Mutable State
File: src/utils.js:9-10
Description: `globalCache = {}` e `totalRevenue = 0` sao variaveis globais mutaveis. Cache sem expiracao, sem limite de tamanho, sem limpeza. `totalRevenue` exportado mas nunca utilizado.
Impact: Memory leak potencial — cache cresce indefinidamente. Estado global compartilhado entre requests.
Recommendation: Usar solucao de cache adequada (Redis, node-cache com TTL). Remover variaveis nao utilizadas.

### [MEDIUM] No Input Validation
File: src/AppManager.js:29-33
Description: Dados do request usados diretamente sem validacao: `const u = req.body.usr`, `const cc = req.body.card`. Nomes de variaveis abreviados (`u`, `e`, `p`, `cid`, `cc`) dificultam compreensao. Nenhuma validacao de formato de email, forca de senha, formato de cartao.
Impact: Dados invalidos entram no sistema. Aplicacao pode crashar com inputs inesperados.
Recommendation: Implementar validacao com biblioteca (Joi, Zod). Usar nomes descritivos: `username`, `email`, `password`, `courseId`, `cardNumber`.

### [MEDIUM] Trivial Payment Validation
File: src/AppManager.js:45-46
Description: Logica de pagamento baseada apenas no prefixo do cartao: `card.startsWith("4")` = PAID, qualquer outro = DENIED. Sem integracao real com gateway de pagamento. Senha padrao `"123456"` quando nao fornecida (linha 68).
Impact: Sistema de pagamento completamente inseguro. Qualquer numero comecando com "4" e aceito.
Recommendation: Integrar com gateway de pagamento real (Stripe, PagSeguro). Implementar validacao adequada de cartao.

### [MEDIUM] Deprecated API Usage
File: src/AppManager.js (callback-based sqlite3)
Description: Uso de API callback-based do sqlite3 ao inves de Promises/async-await moderno. Padroes como `db.get(sql, params, callback)` e `db.run(sql, params, callback)` sao considerados legado.
Impact: Codigo dificil de manter. Tratamento de erros propenso a falhas. Nao aproveita recursos modernos do Node.js.
Recommendation: Usar wrappers Promise ou migrar para `better-sqlite3` que suporta API sincrona. Refatorar para async/await.

### [LOW] Inconsistent Response Format
File: src/AppManager.js:60, 87, 135
Description: POST /checkout retorna JSON `{ msg, enrollment_id }`. GET /admin/financial-report retorna array JSON. DELETE /users retorna texto plano. Sem padrao de resposta consistente.
Impact: Clientes da API precisam tratar diferentes formatos de resposta. Dificulta integracao.
Recommendation: Padronizar respostas: `{ success: true, data: {...} }` para sucesso, `{ success: false, error: "..." }` para erro.

### [LOW] Magic Numbers and Poor Naming
File: src/AppManager.js:29-33, src/AppManager.js:46, src/AppManager.js:68
Description: Variaveis com nomes de uma letra: `u`, `e`, `p`, `cid`, `cc`. Validacao de cartao com magic string `"4"`. Senha padrao `"123456"` hardcoded. Porta 3000 hardcoded em utils.js:6.
Impact: Codigo ilegivel. Dificil para novos desenvolvedores entenderem a logica.
Recommendation: Usar nomes descritivos. Definir constantes em modulo de configuracao.

================================
Total: 12 findings
================================
```
