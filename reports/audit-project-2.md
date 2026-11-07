```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Node.js (JavaScript)
Framework:     Express 4.18.2
Dependencies:  express, sqlite3 (callback API)
Domain:        LMS com fluxo de checkout (users, courses, enrollments,
               payments, audit_logs)
Architecture:  Monolítica — God Class `AppManager` concentra init de banco,
               rotas, regra de negócio e pagamento; `utils.js` guarda segredos
               e estado global mutável
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   3 analyzed | ~181 lines of code
Date:    2026-11-07

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Credenciais e chaves hardcoded (AP-02)
File: src/utils.js:1-7
Description: `dbPass`, `paymentGatewayKey` (`pk_live_...`) e `smtpUser` estão
embutidos no código como objeto `config`.
Impact: Chave de produção de gateway de pagamento e senha de banco expostas no
repositório — comprometimento financeiro direto.
Recommendation: Mover tudo para variáveis de ambiente (`.env` + `.env.example`)
e carregar via `process.env` (T-01).

### [CRITICAL] Log de dados sensíveis (cartão + chave do gateway) (AP-02, AP-15)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
registra o número de cartão completo e a chave do gateway em texto puro.
Impact: Vazamento de PII/PCI e de segredo em qualquer coletor de logs.
Recommendation: Nunca logar cartão/segredo; usar logger com dados mascarados (T-14).

### [CRITICAL] Hash de senha caseiro e inseguro (AP-04)
File: src/utils.js:17-23; src/AppManager.js:68
Description: `badCrypto` concatena pedaços de base64 do `pwd` num loop e corta
em 10 chars. Não é hash criptográfico — é reversível/colidível e usa senha
default `"123456"` quando ausente.
Impact: Senhas trivialmente recuperáveis; contas comprometidas.
Recommendation: Hash forte com salt (`crypto.scrypt`/bcrypt/argon2) (T-05).

### [CRITICAL] God Class — AppManager faz tudo (AP-01)
File: src/AppManager.js:1-141
Description: Uma única classe cria o schema do banco, define todas as rotas,
executa regra de negócio de checkout, processa "pagamento" e grava auditoria.
Impact: Impossível testar isoladamente; acoplamento total; qualquer mudança
arrisca o fluxo inteiro.
Recommendation: Separar em config/database, models (repositories), services,
controllers, routes e middlewares (T-03, T-04).

### [HIGH] Regra de negócio e efeitos colaterais na rota (AP-05)
File: src/AppManager.js:28-78
Description: O handler de `/api/checkout` concentra busca de curso, find-or-create
de usuário, decisão de pagamento, matrícula, pagamento e auditoria inline.
Impact: Fluxo de negócio não reutilizável nem testável sem HTTP.
Recommendation: Extrair para `CheckoutService` com repositórios injetados (T-04).

### [HIGH] Callback hell / fluxo assíncrono aninhado (AP-08)
File: src/AppManager.js:37-77, 83-128
Description: Checkout com 4+ níveis de callbacks aninhados; relatório financeiro
usa contadores manuais (`coursesPending--`, `enrPending--`) para saber quando
responder, com risco de `res.json` duplicado.
Impact: Ilegível, propenso a bugs de concorrência e respostas duplicadas.
Recommendation: Promisificar o sqlite3 e usar `async/await` (T-07).

### [HIGH] Estado global mutável (AP-06)
File: src/utils.js:9-10, 12-15
Description: `globalCache = {}` e `totalRevenue = 0` em escopo de módulo, mutados
por `logAndCache`.
Impact: Estado compartilhado entre requisições; vazamento e condições de corrida.
Recommendation: Encapsular cache/estado em serviço injetável (T-06).

### [HIGH] Ausência de injeção de dependência (AP-07)
File: src/AppManager.js:6-8, 1-2
Description: `AppManager` instancia o próprio `sqlite3.Database` e importa
`config`/utils diretamente; não há como injetar um banco de teste.
Impact: Baixa testabilidade e forte acoplamento à infraestrutura.
Recommendation: Injetar conexão e repositórios via construtor no composition root (T-06).

### [MEDIUM] Query N+1 no relatório financeiro (AP-09)
File: src/AppManager.js:83-128
Description: Para cada curso, consulta matrículas; para cada matrícula, consulta
usuário e pagamento separadamente.
Impact: Explosão de queries proporcional a cursos × matrículas.
Recommendation: Substituir por JOIN/agregação única (T-08).

### [MEDIUM] Validação de entrada fraca/ausente (AP-10)
File: src/AppManager.js:29-35, 46
Description: Campos crípticos (`usr/eml/pwd/c_id/card`) com validação mínima; a
"aprovação" do cartão é `cc.startsWith("4")`, sem qualquer validação real.
Impact: Entradas inválidas chegam à regra de negócio; lógica de pagamento falsa
e frágil.
Recommendation: Validação central de payload antes do service (T-09).

### [MEDIUM] Deleção deixa dados órfãos (AP-12)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` remove o usuário mas deixa matrículas e
pagamentos órfãos — a própria resposta admite "ficaram sujos no banco".
Impact: Integridade referencial quebrada.
Recommendation: Deleção em cascata dentro de uma transação (T-12).

### [MEDIUM] Uso de API legada do sqlite3 (callbacks) — deprecated (AP-13)
File: src/AppManager.js:11-22, 37-128; src/app.js:9
Description: Todo o acesso usa a API baseada em callbacks do `sqlite3`, estilo
legado que leva ao callback hell.
Impact: Código difícil de compor; sem suporte nativo a `async/await`.
Recommendation: Promisificar (`util.promisify`) ou migrar para `better-sqlite3`/
driver com Promises (T-07, T-13).

### [MEDIUM] Error handling ad hoc e inconsistente (AP-14)
File: src/AppManager.js:38, 41, 51, 55, 70, 84
Description: Cada callback trata erro à sua maneira (`res.status(500).send("Erro DB")`,
`"Erro Matrícula"`, etc.), sem padrão nem middleware central.
Impact: Respostas de erro inconsistentes e difíceis de manter.
Recommendation: Middleware de erro centralizado no Express (T-11).

### [LOW] Nomes de variáveis crípticos (AP-16)
File: src/AppManager.js:29-33
Description: `u`, `e`, `p`, `cid`, `cc` para usuário, email, senha, course id e cartão.
Impact: Baixa legibilidade.
Recommendation: Nomes descritivos.

### [LOW] console.log como logging de produção (AP-15)
File: src/AppManager.js:45; src/utils.js:13
Description: `console.log` usado como log de aplicação.
Impact: Ruído e ausência de níveis de log.
Recommendation: Logger configurável (T-14).

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
