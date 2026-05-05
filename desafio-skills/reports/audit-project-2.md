# Relatório de auditoria — Projeto 2 (`ecommerce-api-legacy`)

**Stack detectada:** Node.js + Express + `sqlite3` (SQLite em memória)  
**Domínio:** LMS com checkout de cursos e relatório financeiro  
**Arquitetura (pré-refatoração):** `AppManager` concentrando DB, rotas e fluxo de pagamento; utilitários com segredos globais.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express
Files:   3 principais analisados (pré-refatoração)

## Summary
CRITICAL: 1 | HIGH: 3 | MEDIUM: 2 | LOW: 1

## Findings

### [CRITICAL] Credenciais e chaves hardcoded no repositório
File: utils.js:1-7 (legado; arquivo removido na Fase 3)
Description: Objeto `config` continha senhas fictícias de DB, chave de gateway e usuário SMTP versionados.
Impact: Vazamento de segredos e má prática irreversível em histórico sem rotação.
Recommendation: `process.env` obrigatório; falhar startup se segredos de produção ausentes.

### [HIGH] God Class (`AppManager`)
File: AppManager.js:1-141 (legado)
Description: Classe única com `initDb`, definição de rotas e orquestração de checkout/relatório.
Impact: MVC ausente; difícil testar unidades e substituir persistência.
Recommendation: Serviços (`CheckoutService`, `ReportService`) + camada de dados + rotas finas.

### [HIGH] Função criptográfica custom inadequada para senhas
File: utils.js:17-23 `badCrypto` (legado)
Description: “Hash” derivado de concatenação base64 em loop, truncado.
Impact: Não é KDF; armazenamento fraco de credenciais.
Recommendation: `crypto.scrypt` nativo ou `bcrypt`/argon2; `verify` com comparação em tempo constante.

### [HIGH] Dados sensíveis em logs
File: AppManager.js:45 (legado)
Description: Log de número de cartão e chave de gateway.
Impact: PCI/PII em logs; compliance impossível.
Recommendation: Log apenas IDs/mascarados; nunca PAN completo.

### [MEDIUM] Padrão N+1 no relatório financeiro
File: AppManager.js:80-128 (legado)
Description: `forEach` de cursos com queries encadeadas por matrícula, usuário e pagamento.
Impact: Latência cresce com matrículas.
Recommendation: JOIN único ou agregação SQL + montagem em memória O(n).

### [MEDIUM] Callback pyramid no checkout
File: AppManager.js:37-77 (legado)
Description: Aninhamento profundo de callbacks `sqlite3`.
Impact: Erros e fluxos difíceis de manter; risco de race em respostas HTTP.
Recommendation: Promises/`async-await` com wrappers em `db.run/get/all`.

### [LOW] Nomenclatura de uma letra em payload de API
File: AppManager.js:28-33 (legado)
Description: `u`, `e`, `p`, `cid`, `cc`.
Impact: Legibilidade e revisão de segurança prejudicadas.
Recommendation: Nomes descritivos (`userName`, `email`, ...).

### [MEDIUM] APIs deprecated — verificação
File: N/A
Description: Não identificado `req.param()` ou `new Buffer()`; uso majoritariamente de APIs Express 4.x atuais. Registrado como verificação explícita.
Impact: Baixo hoje; risco futuro se dependências envelhecerem.
Recommendation: Manter `package-lock.json` e auditoria `npm audit`.

================================
Total: 8 findings
================================
```

**Nota pós-refatoração:** código reorganizado em `src/config.js`, `src/database.js`, `src/services/*`, `src/routes.js`, `src/password.js` (scrypt), `src/cache.js`. Segredos não possuem mais defaults “de produção” no fonte.
