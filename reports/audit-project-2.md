# ARCHITECTURE AUDIT REPORT

**Project:** ecommerce-api-legacy
**Stack:** JavaScript (Node.js) + Express 4.18.2 + SQLite
**Files:** 3 analyzed | ~278 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Production Secrets
File: `src/utils.js:1-7`
Description: Credenciais de produção hardcoded: `dbPass: 'senha_super_secreta_prod_123'`, `paymentGatewayKey: 'pk_live_1234567890abcdef'`, `smtpUser`.
Impact: Vazamento de segredos em qualquer controle de versão; acesso indevido a gateways de pagamento e SMTP.
Recommendation: Mover para `process.env` (e.g. `config/index.js` lendo `PAYMENT_GATEWAY_KEY`, `SMTP_USER`) e não commitar valores reais.

### [CRITICAL] Insecure Custom Hashing (badCrypto)
**File:** `src/utils.js:17-23`
Description: `badCrypto()` faz "hash" concatenando `base64` dos primeiros 2 bytes 10.000× — reversível e não é criptografia. Usado no login de usuários (AppManager.js:68).
Impact: Senhas de todos os usuários são falsamente "protegidas" e trivialmente decifráveis.
Recommendation: Substituir por `bcrypt`/`crypto.scrypt` (`utils/security.js` → `hashPassword`).

### [CRITICAL] Unauthenticated Financial Report (Backdoor)
**Location:** `src/AppManager.js:80-129`
Description: `GET /api/admin/financial-report` expõe receita, alunos e valores de pagamento sem qualquer autenticação; qualquer cliente pode ler dados financeiros.
Impact: Exposição total de dados sensíveis da plataforma.
Recommendation: Proteger com middleware de auth de admin (`requireAdmin`), exigindo token via env.

### [CRITICAL] Global Mutable State
**Location:** `src/utils.js:9-10`
Description: `globalCache` e `totalRevenue` como variáveis globais mutáveis exportadas e alteradas em runtime.
Impact: Comportamento imprevisível, corrida em concorrência.
Recommendation: Estado scoped por requisição/request; cache via `Map` encapsulado (não exportado mutável).

### [CRITICAL] Weak Default Credentials / Seed
**Location:** `src/AppManager.js:18`
Description: Usuário seedado com senha em texto puro `'123'` e hash inseguro para novos usuários; adição de entradas sem validação de força de senha.
Impact: Acesso trivial à conta admin/semente.
Recommendation: Forçar mínimo de 6 caracteres, usar bcrypt no seed e não salvar senha em texto.

### [HIGH] God Class AppManager
**Location:** `src/AppManager.js:4`
Description: Uma única classe acumula conexão, schema, rotas, checkout, pagamento, matrícula, relatório e deleção — 4 concerns num arquivo.
Impact: Inviável de testar em isolado; alta acoplamento.
Recommendation: Split em camadas MVC: `models/`, `services/`, `controllers/`, `routes/`, `middlewares/`.

### [HIGH] Business Logic Inside Routes
**Location:** `src/AppManager.js:28-78`
Description: Todo o fluxo de checkout (validação, consulta de curso, hash, pagamento, matrícula, audit) dentro do handler HTTP.
Recommendation: Extrair para `checkoutService.processCheckout()`; rota fica fina.

### [HIGH] Non-standardized Error Handling
**Location:** `src/AppManager.js` (vários)
Description: Respostas de erro como strings HTML soltas (`res.send("Bad Request")`), erros `500` sem corpo estruturado, `next` sem uso.
Recommendation: Middleware de erro centralizado devolvendo JSON (`errorHandler`).

### [MEDIUM] N+1 Queries (Financial Report)
**Location:** `src/AppManager.js:89-127`
Description: Relatório aninha `courses.forEach → enrollments.forEach → users/payments` com múltiplas queries por linha (padrão N+1).
Impact: Degradação clara de performance.
Recommendation: Consulta agregada única com JOIN (`getReportData`).

### [MEDIUM] Duplicate Checkout/Enrollment Logic
**Location:** `src/AppManager.js:50-62`
Description: Matrícula + pagamento + audit_log em blocos quase duplicados nos dois caminhos (novo usuário / usuário existente).
Recommendation: Unificar em um único fluxo no service.

### [MEDIUM] Orphan data on user deletion
**Location:** `src/AppManager.js:131-137`
Description: `DELETE /api/users/:id` remove o usuário mas deixa matrículas/pagamentos órfãos no banco, sem transação.
Recommendation: Transação que remove matrículas/pagamentos associados antes do usuário (`userModel.deleteById`).

### [LOW] Enigmatic Names / Magic Numbers
**Location:** `src/AppManager.js:28-36`
Description: Propriedades obscuras (`usr`, `eml`, `pwd`, `c_id`, `cc`); cartão baseado em `startsWith('4')` sem constante.
Impact: Legibilidade reduzida.
Recommendation: Renomear para descritivos; extrair regra para helper.

### [LOW] No input length/type validation
**Location:** `src/AppManager.js:35`
Description: A checagem é só presença de campos; tipos e limites (ex: tamanho de card/email) sem validação.
Recommendation: Validar tipos e comprimentos no service (`validateInput`).

---
**Total: 13 findings** (ordenação por severidade CRITICAL → LOW)