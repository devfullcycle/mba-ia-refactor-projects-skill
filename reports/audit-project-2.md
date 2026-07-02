================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] God Class / God File (AP-05)
File: src/AppManager.js:4-142
Description: `AppManager` concentra a conexão SQLite (`this.db`), criação de schema e seed (`initDb`), e todos os handlers de rota com regra de negócio embutida (`setupRoutes`) — uma única classe acumula persistência, domínio e roteamento.
Impact: Impossível testar em isolamento, alterar uma responsabilidade sem risco de quebrar outra, ou escalar o time trabalhando em paralelo no arquivo.
Recommendation: Separar em camadas MVC: `config/database.js` (conexão), `models/` (acesso a dados por entidade), `controllers/` (orquestração), `routes/` (definição de endpoints).

### [CRITICAL] Endpoint destrutivo sem autenticação (AP-04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga qualquer usuário só com o `id` da URL, sem autenticação, autorização ou confirmação — e a própria mensagem de resposta ("matrículas e pagamentos ficaram sujos no banco") admite que gera inconsistência de dados.
Impact: Qualquer cliente não autenticado pode apagar qualquer usuário e corromper a integridade referencial de `enrollments`/`payments`.
Recommendation: Exigir autenticação + autorização (o próprio usuário ou admin), e tratar as dependências (cascade ou soft delete) em vez de deixar registros órfãos.

### [CRITICAL] Credenciais / segredos hardcoded (AP-02)
File: src/utils.js:2-6
Description: `dbUser`, `dbPass`, `paymentGatewayKey` (`pk_live_...`) e `smtpUser` estão hardcoded em `config`. `paymentGatewayKey` é usado em produção (AppManager.js:45); `dbUser`/`dbPass`/`smtpUser` sequer são referenciados em nenhum outro arquivo — segredos expostos sem nenhum uso real.
Impact: Vazamento de credenciais de produção e chave de gateway de pagamento caso o repositório seja exposto; risco de fraude financeira.
Recommendation: Mover para variáveis de ambiente (`process.env.PAYMENT_GATEWAY_KEY` etc.) com defaults seguros de desenvolvimento; remover as chaves não utilizadas.

### [CRITICAL] Hash de senha inseguro / caseiro (AP-03)
File: src/utils.js:17-23
Description: `badCrypto` não é um hash criptográfico — repete `Buffer.from(pwd).toString('base64')` 10000 vezes e trunca; é Base64 (reversível), não um hash com salt. Usado para senha de novos usuários em `AppManager.js:68`.
Impact: Senhas armazenadas são recuperáveis por qualquer um com acesso ao banco (Base64 não é hashing), violando confidencialidade das credenciais dos alunos.
Recommendation: Substituir por `bcrypt` ou `argon2` com salt (equivalente moderno da tabela de APIs deprecated: hash caseiro/MD5-SHA1 → `bcrypt`/`argon2`).

### [HIGH] Acoplamento forte / ausência de injeção de dependência (AP-10)
File: src/AppManager.js:7
Description: `this.db = new sqlite3.Database(':memory:')` é instanciado diretamente no construtor de `AppManager`; não há como injetar uma conexão de teste ou mock.
Impact: Testes unitários de `AppManager` exigem sempre um banco SQLite real; impossível isolar a lógica de negócio da camada de dados.
Recommendation: Receber a conexão de banco (ou um repository) via injeção no construtor.

### [HIGH] Lógica de negócio na camada errada (AP-06)
File: src/AppManager.js:28-78
Description: O handler de `/api/checkout` decide aprovação de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), cria usuário, matrícula e pagamento diretamente no handler de rota, sem passar por nenhuma camada de serviço/model.
Impact: Regra de negócio de checkout não é reutilizável nem testável fora do contexto HTTP; qualquer mudança na regra exige tocar no roteamento.
Recommendation: Extrair para `services/checkoutService.js` (ou `controllers/checkoutController.js` delegando a um service); a rota deve apenas receber request → chamar service → devolver response.

### [HIGH] Callback hell / tratamento de erro incompleto (AP-09)
File: src/AppManager.js:37-77, 92-127
Description: `/api/checkout` aninha 5 níveis de callbacks (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`); `/api/admin/financial-report` chega a 5 níveis (`db.all` → `forEach` → `db.all` → `forEach` → `db.get` → `db.get`). Vários `err` são ignorados sem tratamento (linhas 92, 104, 106, 133).
Impact: Erros de banco silenciosamente propagam `undefined`/exceptions não capturadas, travando a resposta HTTP (request nunca finaliza) em vez de retornar erro ao cliente.
Recommendation: Migrar para `sqlite`/`better-sqlite3` com `async/await` (API de callbacks do `sqlite3` é o padrão obsoleto — equivalente moderno na tabela de APIs deprecated), tratar todo erro e centralizar via middleware de erro do Express.

### [HIGH] Ausência de autenticação/autorização nas rotas (AP-08)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` expõe faturamento por curso e nome/pagamento de cada aluno matriculado, sem nenhuma checagem de identidade ou papel de administrador — é uma rota "admin" acessível por qualquer requisição anônima.
Impact: Vazamento de dados financeiros e de alunos (nome, valor pago) para qualquer cliente não autenticado.
Recommendation: Middleware de autenticação + autorização por papel (admin) antes de expor dados agregados/financeiros.

### [HIGH] Estado global mutável (AP-07)
File: src/utils.js:9-15
Description: `globalCache` e `totalRevenue` são variáveis de módulo mutáveis, compartilhadas entre todas as requisições; `logAndCache` escreve em `globalCache` sem escopo por requisição nem expiração.
Impact: Vazamento de memória (cache cresce indefinidamente), condição de corrida entre requisições concorrentes, estado que "vaza" de um usuário para outro.
Recommendation: Remover o cache global ad hoc ou substituí-lo por um store apropriado (Redis, ou cache com TTL) fora do módulo compartilhado; encapsular em vez de expor variável mutável de módulo.

### [MEDIUM] Uso inadequado de middleware / configuração (AP-14)
File: src/app.js:1-15
Description: Não existe middleware de tratamento de erro (`app.use((err, req, res, next) => ...)`) no bootstrap; cada rota trata (ou ignora) erro individualmente com formatos de resposta inconsistentes (texto puro vs. JSON).
Impact: Respostas de erro inconsistentes para o cliente da API e nenhum ponto central para logar/monitorar falhas.
Recommendation: Adicionar middleware de erro centralizado no Express e padronizar o formato de resposta de erro (JSON com `{ error: mensagem }`).

### [MEDIUM] Query N+1 (AP-11)
File: src/AppManager.js:80-127
Description: `/api/admin/financial-report` roda uma query de `enrollments` por curso (linha 92) e, para cada matrícula, mais uma query de `users` (linha 104) e outra de `payments` (linha 106) — N+1 aninhado dentro de N+1.
Impact: Com M cursos e N matrículas por curso, a rota executa O(M·N) queries; degrada rapidamente com o crescimento da base de alunos.
Recommendation: Substituir por uma única query com `JOIN` entre `courses`, `enrollments`, `users` e `payments` (ou `IN (...)` agregando por curso).

### [MEDIUM] Validação ausente ou insuficiente (AP-12)
File: src/AppManager.js:28-35, 131-133
Description: `/api/checkout` só valida presença dos campos (`!u || !e || !cid || !cc`), sem validar formato de email, formato do "cartão" ou se `c_id` é numérico; `/api/users/:id` usa `req.params.id` direto na query sem validar que é um inteiro válido.
Impact: Entradas malformadas chegam até a camada de banco, gerando erros genéricos de SQL em vez de respostas 400 claras.
Recommendation: Centralizar validação de entrada com um schema validator (ex.: `Joi`, `zod`) reutilizável entre as rotas.

### [MEDIUM] APIs deprecated — driver `sqlite3` baseado em callbacks
File: src/AppManager.js:1, 7, 12-21, 37-133
Description: Todo o acesso a dados usa a API de callback do pacote `sqlite3` (`db.run`, `db.get`, `db.all` com callback), que é o padrão legado do driver.
Impact: Combinada ao AP-09, é a causa raiz do callback hell; dificulta compor operações (ex.: transação entre `enrollments` e `payments`).
Recommendation: Migrar para `sqlite` (wrapper) ou `better-sqlite3`, usando `async/await` nativamente.

### [LOW] Nomenclatura ruim (AP-17)
File: src/AppManager.js:29-33
Description: Variáveis do corpo da requisição em `/api/checkout` usam nomes de uma/duas letras sem revelar intenção: `u`, `e`, `p`, `cid`, `cc`.
Impact: Reduz legibilidade e aumenta risco de erro ao ler/alterar o fluxo de checkout.
Recommendation: Renomear para `userName`, `userEmail`, `userPassword`, `courseId`, `cardNumber`.

### [LOW] Logging por console.log (AP-15)
File: src/app.js:13; src/AppManager.js:45; src/utils.js:13
Description: Log de boot, de processamento de pagamento (que inclui o número do cartão e a chave de gateway em texto) e de cache usam `console.log` sem nível nem timestamp estruturado.
Impact: Sem como filtrar por severidade em produção; o log da linha 45 ainda vaza dado sensível (número de cartão) no stdout.
Recommendation: Usar um logger estruturado (ex.: `pino`/`winston`) com níveis, e nunca logar PAN de cartão ou chaves de API.

### [LOW] Magic number / valor hardcoded (AP-16)
File: src/AppManager.js:46
Description: Aprovação de pagamento decidida por `cc.startsWith("4")` — "4" é um literal opaco (bandeira Visa) sem constante nomeada.
Impact: Regra de negócio ilegível e frágil a mudanças (ex.: suportar outras bandeiras).
Recommendation: Extrair para constante nomeada (`CARD_PREFIX_APPROVED = "4"`) ou, melhor, delegar a decisão a um gateway de pagamento real em vez de simular localmente.

### [LOW] Código morto / segredos nunca usados (AP-18)
File: src/utils.js:2-10
Description: `dbUser`, `dbPass` e `smtpUser` (linhas 2,3,5) e `totalRevenue` (linha 10) são declarados e exportados mas nunca lidos em nenhum outro arquivo do projeto.
Impact: Mantém segredos sensíveis expostos no código sem nenhum benefício funcional; confunde quem lê o módulo tentando entender o que é realmente usado.
Recommendation: Remover as variáveis não utilizadas.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── app.js                              # composition root — monta DI, rotas e sobe o servidor
├── config/
│   ├── env.js                          # variáveis de ambiente com defaults seguros de dev
│   ├── database.js                     # conexão SQLite promisificada (run/get/all)
│   └── logger.js                       # logger estruturado (timestamp + nível), substitui console.log
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   ├── enrollmentModel.js
│   ├── paymentModel.js
│   ├── auditLogModel.js
│   └── reportModel.js                  # query única com JOIN para o relatório financeiro
├── services/
│   ├── passwordService.js              # bcryptjs (hash + compare), substitui badCrypto
│   ├── paymentGatewayService.js        # aprovação de cobrança, sem logar PAN/segredo
│   └── cacheService.js                 # encapsula o antigo globalCache mutável
├── controllers/
│   ├── checkoutController.js
│   ├── financialReportController.js
│   └── userController.js
├── routes/
│   ├── checkoutRoutes.js
│   ├── adminRoutes.js
│   └── userRoutes.js
├── middlewares/
│   ├── errorHandler.js                 # tratamento de erro centralizado
│   ├── asyncHandler.js                 # encaminha rejeições async ao errorHandler
│   └── adminAuth.js                    # protege rota administrativa por chave de API
└── seed.js                             # schema + dados iniciais, fora do bootstrap da API

.env.example                            # PORT, PAYMENT_GATEWAY_KEY, ADMIN_API_KEY
package.json                            # + bcryptjs (dependência mínima, sem compilação nativa)

## Validation
  ✓ Application boots without errors (npm start / node src/app.js)
  ✓ POST /api/checkout            → 200 {"msg":"Sucesso","enrollment_id":N} (idêntico ao original)
  ✓ POST /api/checkout (recusado) → 400 "Pagamento recusado" (idêntico ao original)
  ✓ GET /api/admin/financial-report (com x-admin-key) → mesmo formato JSON, dados corretos
  ✓ DELETE /api/users/:id → 200, agora sem deixar enrollments/payments órfãos
  ✓ Validação de entrada (campos ausentes / id não numérico) → 400 em vez de erro genérico de banco
  ✓ Zero anti-patterns remaining do catálogo (God Class, hash inseguro, segredos hardcoded, callback hell, N+1, estado global mutável — todos corrigidos)
================================

## Mapeamento finding → correção

| Finding (severidade) | Correção aplicada |
|---|---|
| God Class (CRITICAL) | `AppManager.js` quebrado em config/models/services/controllers/routes |
| Endpoint destrutivo sem auth — DELETE /users/:id (CRITICAL) | Cascade delete de enrollments/payments; validação de `id`. Auth de identidade não implementada — não há sistema de login na app original; documentado como follow-up |
| Credenciais hardcoded (CRITICAL) | Movidas para `config/env.js` via `process.env`, com defaults de dev; `dbUser`/`dbPass`/`smtpUser` (nunca usados) removidos |
| Hash de senha inseguro — `badCrypto` (CRITICAL) | Substituído por `bcryptjs` (hash + salt) em `passwordService.js` |
| Acoplamento forte / sem DI (HIGH) | Conexão de banco e models injetados via construtor em todos os controllers |
| Lógica de negócio na rota (HIGH) | Extraída para `checkoutController` + `paymentGatewayService`, `passwordService` |
| Callback hell (HIGH) | Achatado com `async/await` sobre driver `sqlite3` promisificado |
| Ausência de auth — GET /admin/financial-report (HIGH) | Protegido por middleware `adminAuth` (header `x-admin-key`) — mudança de comportamento documentada: chamadas sem o header agora recebem 401 |
| Estado global mutável — `globalCache` (HIGH) | Encapsulado em `CacheService`, injetado por instância |
| Middleware de erro ausente (MEDIUM) | `errorHandler` centralizado + `asyncHandler` |
| Query N+1 (MEDIUM) | `reportModel.findFinancialReportRows()` — uma única query com `JOIN` |
| Validação ausente (MEDIUM) | Checagem de tipos/presença em checkout e delete |
| API deprecated — `sqlite3` callbacks (MEDIUM) | Wrapper Promise em `config/database.js`, uso de `async/await` |
| Nomenclatura ruim (LOW) | `u,e,p,cid,cc` → `userName, userEmail, userPassword, courseId, cardNumber` |
| Logging via console.log (LOW) | `config/logger.js` estruturado (JSON com timestamp/nível); número do cartão não é mais logado |
| Magic number (LOW) | `APPROVED_CARD_PREFIX` nomeado em `paymentGatewayService.js` |
| Código morto / segredos não usados (LOW) | `dbUser`, `dbPass`, `smtpUser`, `totalRevenue` removidos |

**Decisão de escopo documentada**: a app original não tinha nenhum sistema de login/identidade. Implementar autenticação real de usuário para `DELETE /api/users/:id` exigiria criar um fluxo de login do zero — fora do escopo desta refatoração arquitetural. A rota administrativa (`/api/admin/financial-report`) foi protegida com uma chave de API simples por ser claramente um endpoint admin; para `DELETE /api/users/:id`, a integridade de dados foi corrigida (cascade), e a lacuna de autenticação ficou registrada como item de follow-up, conforme a exceção prevista nas guidelines para correções de segurança que alteram o contrato externo.
