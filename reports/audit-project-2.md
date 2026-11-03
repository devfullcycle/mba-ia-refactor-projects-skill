```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — engines não declarado; local v25.9.0)
Framework:     Express 4.22.1 (range ^4.18.2)
Dependencies:  express, sqlite3 5.1.7
Domain:        LMS API com fluxo de checkout (usuários, cursos, matrículas, pagamentos, auditoria)
Architecture:  Monolito "God Class" — AppManager cria o banco, faz seed, define rotas, SQL e regra de pagamento
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória)
Entry point:   src/app.js — `npm start` — porta 3000 (config.port)
Endpoints:     3 routes mapped
================================
```

| Método | Path | Handler |
|---|---|---|
| POST | `/api/checkout` | src/AppManager.js:28 (callback inline) |
| GET | `/api/admin/financial-report` | src/AppManager.js:80 (callback inline) |
| DELETE | `/api/users/:id` | src/AppManager.js:131 (callback inline) |

````
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### F-01 [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139
Evidence:
```js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { ... }        // linhas 10-23: schema + seed
    setupRoutes(app) { ... } // linhas 25-138: rotas + SQL + pagamento + auditoria + relatório
```
Description: Uma única classe é dona da conexão, do schema, do seed, das 3 rotas, das queries, da regra de aprovação de pagamento, do cache e do relatório financeiro.
Impact: Nada pode ser testado isoladamente; qualquer alteração (ex.: trocar gateway de pagamento) exige mexer na classe inteira.
Recommendation: Decompor em database/, models/, services/, controllers/, views/ com composition root em src/app.js (PB-03, PB-09).

### F-02 [CRITICAL] Credenciais hardcoded (AP-02)
File: src/utils.js:1-7
Evidence:
```js
dbPass: "senha_super_secreta_prod_123",
paymentGatewayKey: "pk_live_1234567890abcdef",
```
Description: Senha de banco de produção, chave live do gateway de pagamento e usuário SMTP versionados no código.
Impact: Qualquer pessoa com acesso ao repositório pode efetuar cobranças/estornos com a chave live e acessar o banco.
Recommendation: `src/config` lendo `process.env` + `.env.example` sem valores reais (PB-02).

### F-03 [CRITICAL] Exposição de dados sensíveis em log (AP-04)
File: src/AppManager.js:45
Evidence:
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
Description: Número completo do cartão e a chave do gateway são impressos em todo checkout.
Impact: Violação PCI-DSS; logs passam a conter dados de cartão e segredo de pagamento.
Recommendation: Mascarar cartão (últimos 4 dígitos) e nunca logar segredos (PB-04).

### F-04 [CRITICAL] Armazenamento inseguro de senha (AP-06)
File: src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18
Evidence:
```js
for(let i = 0; i < 10000; i++) {
    hash += Buffer.from(pwd).toString('base64').substring(0, 2);
}
let hash = badCrypto(p || "123456");
```
Description: "Hash" caseiro baseado em base64 (reversível, sem salt, 10 caracteres → colisões triviais); senha padrão `123456` atribuída silenciosamente quando `pwd` não é enviado; seed com senha em texto puro.
Impact: Senhas recuperáveis a partir do banco; contas criadas no checkout ficam com senha conhecida publicamente.
Recommendation: `crypto.scrypt` com salt + `timingSafeEqual`; exigir senha para novos usuários (PB-06).

### F-05 [CRITICAL] Endpoints administrativos/destrutivos sem autenticação (AP-05)
File: src/AppManager.js:80, src/AppManager.js:131-137
Evidence:
```js
app.get('/api/admin/financial-report', (req, res) => {
app.delete('/api/users/:id', (req, res) => {
```
Description: Relatório financeiro (nomes de alunos e valores pagos) e exclusão de usuários acessíveis por qualquer cliente anônimo.
Impact: Vazamento de dados financeiros/pessoais e exclusão em massa de contas.
Recommendation: Middleware `requireAdmin` com token vindo da config (PB-05).

### F-06 [HIGH] Callback Hell sem transação (AP-10)
File: src/AppManager.js:37-77
Evidence:
```js
this.db.get(..., (err, course) => {
    this.db.get(..., (err, user) => {
        this.db.run(..., function(err) {
            self.db.run(..., function(err) {
                self.db.run(..., (err) => {
```
Description: Checkout com 5 níveis de callbacks grava usuário, matrícula, pagamento e auditoria sem transação; o usuário é criado antes da decisão de pagamento.
Impact: Falha no meio deixa matrícula sem pagamento (ou usuário órfão quando o pagamento é recusado); fluxo ilegível e difícil de testar.
Recommendation: Wrapper Promise + async/await + `transaction()` atômica (PB-10).

### F-07 [HIGH] Regra de negócio na rota (AP-07)
File: src/AppManager.js:28-78, src/AppManager.js:46
Evidence:
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
Description: Validação, criação de usuário, regra de aprovação de pagamento, matrícula, auditoria e cache implementados dentro do handler HTTP.
Impact: Regra de pagamento não reutilizável nem testável; trocar o gateway exige reescrever a rota.
Recommendation: CheckoutController + PaymentService + Models (PB-07).

### F-08 [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-15, src/utils.js:25
Evidence:
```js
let globalCache = {};
let totalRevenue = 0;
```
Description: Cache e acumulador de receita como variáveis de módulo mutáveis e exportadas.
Impact: Estado compartilhado implícito entre requests, impossível isolar em testes; vazamento de memória (cache sem limite).
Recommendation: `CacheService` instanciado no composition root e injetado (PB-08).

### F-09 [HIGH] Acoplamento forte / sem DI (AP-09)
File: src/AppManager.js:5-8, src/app.js:8-10
Evidence:
```js
constructor() {
    this.db = new sqlite3.Database(':memory:');
}
```
Description: A classe instancia o banco concreto internamente e registra as próprias rotas; não há injeção de dependências.
Impact: Impossível substituir o banco/gateway em testes ou ambientes.
Recommendation: Composition root criando database → models → services → controllers (PB-09).

### F-10 [MEDIUM] Queries N+1 com sincronização manual (AP-13)
File: src/AppManager.js:83-128
Evidence:
```js
courses.forEach(c => {
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
        enrollments.forEach(enr => {
            this.db.get("SELECT name, email FROM users WHERE id = ?", ...
                this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", ...
```
Description: 1 + C + 2·E queries para montar o relatório, sincronizadas por contadores manuais (`coursesPending--`).
Impact: Latência cresce com o número de matrículas; ordem de resposta não determinística.
Recommendation: Uma única query com LEFT JOINs e agregação em memória (PB-12).

### F-11 [MEDIUM] Validação de entrada insuficiente (AP-14)
File: src/AppManager.js:35, src/AppManager.js:131-136
Evidence:
```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```
Description: Apenas presença é checada: sem validação de formato de e-mail, cartão ou id do curso; DELETE não valida `:id` nem se o usuário existe (sempre 200).
Impact: Dados inválidos persistidos e respostas enganosas.
Recommendation: Validators centralizados no controller (PB-13).

### F-12 [MEDIUM] Tratamento de erros inadequado (AP-15)
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135
Evidence:
```js
this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
    let enrPending = enrollments.length;
```
Description: Erros ignorados ou mascarados (erro de banco vira 404 "Curso não encontrado"); em erro na linha 92 `enrollments` é `undefined` e `.length` derruba o processo; não há error handler central.
Impact: Crash do servidor e falhas silenciosas.
Recommendation: Exceções de domínio + `asyncHandler` + middleware de erro (PB-14).

### F-13 [MEDIUM] Integridade referencial ausente (AP-17)
File: src/AppManager.js:131-137, src/AppManager.js:12-16
Evidence:
```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```
Description: Exclusão de usuário mantém matrículas e pagamentos órfãos; tabelas sem FOREIGN KEY.
Impact: Relatórios inconsistentes ("Unknown") e dados financeiros sem dono.
Recommendation: Deleção em cascata transacional + FKs no schema (PB-16).

### F-14 [MEDIUM] Configuração de debug em runtime (AP-12, rebaixado para MEDIUM)
File: src/AppManager.js:1
Evidence:
```js
const sqlite3 = require('sqlite3').verbose();
```
Description: Modo verbose do driver ativado incondicionalmente (stack traces estendidos e overhead). Rebaixado de HIGH: não expõe console remoto.
Impact: Overhead e mensagens internas mais verbosas em produção.
Recommendation: Ativar verbose apenas via config (PB-02).

### F-15 [LOW] Magic numbers / strings (AP-19)
File: src/AppManager.js:46, src/AppManager.js:48, src/utils.js:19, src/utils.js:6
Evidence:
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
Description: Prefixo de cartão aprovado, status de pagamento, número de iterações e porta como literais soltos.
Impact: Regras escondidas e duplicação de strings de status.
Recommendation: Constantes nomeadas no model/service (PB-18).

### F-16 [LOW] Nomenclatura ruim (AP-20)
File: src/AppManager.js:29-33, src/AppManager.js:26, src/utils.js:12, src/utils.js:17
Evidence:
```js
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;
```
Description: Variáveis de uma letra, `self = this`, nomes enganosos (`badCrypto`, `logAndCache`, `AppManager`).
Impact: Leitura difícil e intenção obscura.
Recommendation: Renomear internamente mantendo os nomes do payload (PB-19).

### F-17 [LOW] Código morto (AP-21)
File: src/utils.js:10, src/utils.js:25, src/AppManager.js:2, src/utils.js:2-5
Evidence:
```js
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
```
Description: `totalRevenue` importado e exportado sem uso; `dbUser`, `dbPass`, `smtpUser` nunca lidos.
Impact: Ruído e falsa impressão de funcionalidade.
Recommendation: Remover (PB-19).

### F-18 [LOW] Logging via console.log (AP-22)
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Evidence:
```js
console.log(`[LOG] Salvando no cache: ${key}`);
```
Description: Logs sem nível nem destino configurável.
Impact: Impossível filtrar por severidade; dados sensíveis misturados.
Recommendation: `src/utils/logger.js` com níveis (PB-20).

## Deprecated APIs
None detected. Verificados: `new Buffer()`, `url.parse()`, `.substr()`, `crypto.createCipher()`, `req.param()`, `body-parser`, `res.send(status)`. O código já usa `Buffer.from` e `express.json()`. Observação: o padrão callback do `sqlite3` é legado (não deprecated) e será substituído por async/await (F-06).

## Refactoring Plan (preview of Phase 3)
- Target structure: `src/{config,database,models,services,controllers,views,middlewares,utils}` + `src/app.js` (composition root, `npm start` inalterado)
- F-01, F-09 → PB-03/PB-09: desmontar AppManager
- F-02, F-14 → PB-02: `src/config/index.js` + `.env.example`
- F-03 → PB-04: mascarar cartão; nunca logar chave
- F-04 → PB-06: `crypto.scrypt` com salt; senha obrigatória para novo usuário
- F-05 → PB-05: `requireAdmin` (header `X-Admin-Token`)
- F-06, F-07 → PB-10/PB-07: CheckoutController async + transação + PaymentService
- F-08 → PB-08: CacheService injetado
- F-10 → PB-12: relatório com LEFT JOINs
- F-11, F-12 → PB-13/PB-14: validação + error handler central
- F-13 → PB-16: cascata transacional + FKs
- F-15..F-18 → PB-18/PB-19/PB-20
- Contract changes required for security: `/api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token`; checkout de usuário novo sem `pwd` retorna 400; DELETE de usuário inexistente retorna 404.

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````
