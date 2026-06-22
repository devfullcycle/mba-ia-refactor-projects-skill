# Architecture Audit Report — Projeto 2

> Gerado pela skill `/refactor-arch` — Fase 2: Auditoria

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines de código
         src/app.js, src/AppManager.js, src/utils.js

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 2 | LOW: 2
Total findings: 12

================================
PHASE 1: PROJECT ANALYSIS (recap)
================================
Language:      JavaScript / Node.js
Framework:     Express 4.18.2
Database:      SQLite in-memory (better-sqlite3 / sqlite3)
Domain:        LMS API com fluxo de checkout (cursos, matrículas, pagamentos)
Architecture:  God Class — toda a lógica em AppManager.js: DB, rotas, pagamentos, autenticação, logs
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs
================================
```

---

## Findings

### [CRITICAL] Credenciais Hardcoded em utils.js
**ID:** AP-02  
**File:** `src/utils.js`  
**Lines:** 2–7  
**Description:** `utils.js` expõe diretamente no código: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser: "no-reply@fullcycle.com.br"`. Essas credenciais ficam visíveis a qualquer pessoa com acesso ao repositório.  
**Impact:** Comprometimento do gateway de pagamento e acesso não autorizado ao banco e servidor de email em produção.  
**Fix:** PT-02  
**Recommendation:** Mover todas as credenciais para variáveis de ambiente via `dotenv` e nunca commitar valores reais.

---

### [CRITICAL] God Class — AppManager com Todas as Responsabilidades
**ID:** AP-03  
**File:** `src/AppManager.js`  
**Lines:** 1–120 (arquivo completo)  
**Description:** A classe `AppManager` mistura em um único arquivo: inicialização do banco (`initDb()`), configuração de rotas Express (`setupRoutes()`), lógica de checkout com processamento de pagamento, criação de usuário, matrícula, registro de auditoria e logging — tudo dentro do mesmo método `setupRoutes()`. Nenhuma separação de camadas.  
**Impact:** Impossível testar qualquer componente isoladamente. Qualquer mudança em uma funcionalidade afeta todas as outras.  
**Fix:** PT-03  
**Recommendation:** Separar em Models (userModel, courseModel), Controllers (checkoutController, reportController), Routes (checkoutRoutes, reportRoutes) e Services (paymentService).

---

### [CRITICAL] Senha com Algoritmo Criptográfico Inválido (badCrypto)
**ID:** AP-05  
**File:** `src/utils.js`, `src/AppManager.js`  
**Lines:** `utils.js:15–21`, `AppManager.js:55`  
**Description:** A função `badCrypto()` implementa um "hash" customizado que apenas repete base64 do input 10.000 vezes e trunca em 10 chars — isso NÃO é criptografia real. Senhas armazenadas via `badCrypto(p || "123456")` são trivialmente reversíveis. O login não valida senha (busca apenas por email e aceita qualquer usuário existente).  
**Impact:** Qualquer senha pode ser descoberta. Usuários existentes nunca têm senha validada no checkout.  
**Fix:** PT-04  
**Recommendation:** Substituir `badCrypto` por `bcrypt.hash()` na criação e `bcrypt.compare()` no login.

---

### [CRITICAL] Endpoint Administrativo Sem Autenticação
**ID:** AP-04  
**File:** `src/AppManager.js`  
**Lines:** 68–100  
**Description:** `GET /api/admin/financial-report` retorna dados financeiros completos de todos os cursos, matrículas e alunos sem nenhuma verificação de autenticação ou autorização. Qualquer cliente HTTP pode acessar.  
**Impact:** Exposição de dados financeiros e pessoais de todos os alunos para qualquer chamador anônimo.  
**Fix:** PT-09  
**Recommendation:** Proteger com middleware `requireAdmin` que valide JWT com role admin.

---

### [HIGH] N+1 Queries no Relatório Financeiro
**ID:** AP-10  
**File:** `src/AppManager.js`  
**Lines:** 68–100  
**Description:** `GET /api/admin/financial-report` executa: 1 query para todos os cursos, depois para cada curso: 1 query de matrículas, depois para cada matrícula: 1 query de usuário + 1 query de pagamento. Para 5 cursos com 3 matrículas cada: 1 + 5 + 15 + 15 = 36 queries com callback hell profundo.  
**Impact:** Performance degradada exponencialmente com o crescimento de dados; código ilegível com callbacks aninhados em 4 níveis.  
**Fix:** PT-06  
**Recommendation:** Substituir por uma única query com JOINs em courses, enrollments, users e payments.

---

### [HIGH] Lógica de Pagamento e Negócio Dentro da Rota
**ID:** AP-08  
**File:** `src/AppManager.js`  
**Lines:** 20–65  
**Description:** O handler de `POST /api/checkout` contém: busca de curso, criação de usuário, processamento de pagamento (`cc.startsWith("4")`), inserção de matrícula, inserção de pagamento, log de auditoria e cache — tudo em uma única função de 50 linhas com callbacks aninhados. O processamento de cartão de crédito (mesmo que simulado) está hardcoded na rota.  
**Impact:** Impossível reusar, testar ou substituir a lógica de pagamento sem reescrever a rota inteira.  
**Fix:** PT-08  
**Recommendation:** Extrair para `services/paymentService.js` e `services/enrollmentService.js`.

---

### [HIGH] Cache Global Mutável em utils.js
**ID:** AP-07  
**File:** `src/utils.js`  
**Lines:** 9–10  
**Description:** `let globalCache = {}` e `let totalRevenue = 0` são variáveis de módulo mutáveis compartilhadas globalmente. `logAndCache()` acumula dados no `globalCache` sem limite e sem thread-safety.  
**Impact:** Memory leak em aplicações de longa duração; estado compartilhado entre requisições pode causar comportamento inconsistente.  
**Fix:** PT-05 (adaptar para Node.js)  
**Recommendation:** Remover cache global; se necessário, usar estrutura de cache com TTL (ex: node-cache).

---

### [HIGH] DELETE de Usuário Sem Cascade — Orphaned Records
**ID:** AP-12  
**File:** `src/AppManager.js`  
**Lines:** 101–105  
**Description:** `DELETE /api/users/:id` deleta apenas o usuário mas deixa suas matrículas (`enrollments`) e pagamentos (`payments`) sem referência válida no banco. O próprio código documenta o bug: `res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.")`.  
**Impact:** Dados órfãos que corrompem relatórios financeiros e impedem integridade referencial.  
**Fix:** Adicionar `ON DELETE CASCADE` no schema ou executar DELETEs em cascade no controller.  
**Recommendation:** Usar transação para deletar enrollments e payments antes de deletar o user.

---

### [MEDIUM] Número de Cartão como Magic String para Validação de Pagamento
**ID:** AP-14  
**File:** `src/AppManager.js`  
**Lines:** 42  
**Description:** `cc.startsWith("4")` é a lógica de aprovação de pagamento — cartões que começam com "4" são aprovados, os demais são recusados. Esta regra de negócio está hardcoded como magic string sem nenhuma constante ou serviço.  
**Impact:** Regra de negócio invisível e não documentada; impossível alterar sem entender o contexto.  
**Fix:** PT-12  
**Recommendation:** Extrair para `paymentService.processPayment()` com constante `APPROVED_BIN_PREFIXES`.

---

### [MEDIUM] Ausência de Error Handling Centralizado
**ID:** AP-12  
**File:** `src/AppManager.js`  
**Lines:** Vários (múltiplos `return res.status(500).send("Erro DB")`)  
**Description:** Erros são tratados com strings genéricas espalhadas por todos os handlers: `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`. Não há middleware de error handling do Express, sem formato JSON consistente, sem logging de stack traces.  
**Impact:** Erros silenciados, diagnóstico impossível em produção.  
**Fix:** PT-09 (error handler)  
**Recommendation:** Criar `middlewares/errorHandler.js` com handler de 4 parâmetros do Express.

---

### [LOW] console.log como Logging Operacional
**ID:** AP-13  
**File:** `src/AppManager.js`, `src/utils.js`  
**Lines:** `AppManager.js:42`, `utils.js:13`  
**Description:** `console.log('Processando cartão...')` dentro do checkout e `console.log('[LOG]...')` em `logAndCache()` são usados como logging operacional sem nível, sem estrutura, sem possibilidade de desligar em produção.  
**Impact:** Dados sensíveis de cartão expostos nos logs de produção.  
**Fix:** PT-10  
**Recommendation:** Usar `console.log` com formato estruturado ou biblioteca de logging (pino/winston).

---

### [LOW] Abreviações Incompreensíveis nos Parâmetros de Entrada
**ID:** AP-14  
**File:** `src/AppManager.js`  
**Lines:** 13–17  
**Description:** O endpoint `/api/checkout` usa parâmetros com nomes crípticos: `usr`, `eml`, `pwd`, `c_id`, `card` — sem documentação ou validação que explique o significado. Contratos de API obscuros.  
**Impact:** Dificulta integração, manutenção e debugging por outros desenvolvedores.  
**Fix:** Renomear para `username`, `email`, `password`, `course_id`, `card_number` na validação e documentar.  
**Recommendation:** Padronizar nomes de campos e adicionar OpenAPI/Swagger.

---

```
================================
Phase 2 complete.
Total findings: 12 (4C / 4H / 2M / 2L)

Proceed with Phase 3 — Refactoring? [y/n]
> y
================================
```
