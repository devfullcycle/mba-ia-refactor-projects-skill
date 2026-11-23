# Relatório de Auditoria Arquitetural — ecommerce-api-legacy

================================
ARCHITECTURE AUDIT REPORT (INITIAL)
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express (^4.18.2) + SQLite3 (^5.1.6)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 2 | HIGH: 4 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Exposed Hardcoded Sensitive Credentials & Unmasked Credit Card Logging
File: src/utils.js:1-7
Description: Segredos críticos de infraestrutura e produção estão expostos diretamente no código-fonte no objeto `config`, incluindo senha de banco de dados (`dbPass: "senha_super_secreta_prod_123"`) e chave viva de gateway de pagamento (`paymentGatewayKey: "pk_live_1234567890abcdef"`). Adicionalmente, em `src/AppManager.js:45`, o número completo do cartão de crédito do cliente é impresso em texto claro no console junto à chave do gateway (`console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`).
Impact: Violação direta de normas de segurança e compliance (PCI-DSS, LGPD/GDPR), permitindo que credenciais de produção sejam exfiltradas via repositório de código e que dados de cartão de crédito de clientes fiquem armazenados em logs abertos.
Recommendation: Extrair todas as credenciais sensíveis para variáveis de ambiente (`process.env`) acessíveis através de uma camada isolada `config/index.js` (ou `.env`). Mascarar permanentemente os dados de cartão de crédito antes de qualquer log (exibindo no máximo os 4 últimos dígitos).

### [CRITICAL] Monolithic God Class / God File
File: src/AppManager.js:4-139
Description: A classe `AppManager` concentra todas as responsabilidades do sistema em um único arquivo: inicialização e schema DDL do SQLite (`initDb`), injeção de sementes (seeds), instanciação de rotas HTTP do Express (`setupRoutes`), execução de queries raw SQL, regras de validação de payload, regras de negócio de checkout e pagamento, hashing de senhas, orquestração de matrículas, geração de relatórios e exclusão de entidades.
Impact: Violação gravíssima do Single Responsibility Principle (SRP) e da arquitetura em camadas; torna a aplicação praticamente intestável, com acoplamento rígido que inviabiliza manutenção, evolução e escalabilidade.
Recommendation: Decompor o monólito seguindo o padrão MVC limpo: segregar modelos e acesso ao banco em `models/`, regras e fluxo de negócio em `controllers/`, rotas e transporte HTTP em `routes/`, configurações em `config/` e tratamento de erros em `middlewares/`.

### [HIGH] Direct Database Operations in Controllers/Routes
File: src/AppManager.js:28-137
Description: Todas as interações com o banco de dados (`this.db.get`, `this.db.run`, `this.db.all`) são executadas diretamente dentro dos callbacks de rota do Express (nas rotas `/api/checkout`, `/api/admin/financial-report` e `/api/users/:id`), misturando a camada de transporte com lógica de persistência.
Impact: Forte acoplamento entre o protocolo HTTP e a camada de dados; impossibilita a reutilização de consultas e lógicas de dados em outros contextos (scripts, filas, testes unitários) e dificulta a troca ou evolução do motor de banco.
Recommendation: Encapsular todas as queries SQL em métodos de repositório/model dedicados (`models/Course.js`, `models/User.js`, `models/Enrollment.js`, `models/Payment.js`), deixando para os controllers apenas a orquestração do fluxo de requisição e resposta.

### [HIGH] Broken Cryptography & Weak Insecure Password Hashing
File: src/utils.js:17-23
Description: A função `badCrypto()` implementa um algoritmo caseiro baseado em loop de repetição com `Buffer.from(pwd).toString('base64')` truncando a string para apenas 10 caracteres. Além disso, em `src/AppManager.js:18`, senhas de seed são inseridas em texto puro (`'123'`), e em `src/AppManager.js:68`, é utilizado fallback para senha fraca (`p || "123456"`).
Impact: Os hashes gerados são previsíveis, facilmente reversíveis e vulneráveis a ataques de força bruta e colisão, violando os princípios fundamentais de segurança de armazenamento de senhas.
Recommendation: Substituir o algoritmo inseguro por uma biblioteca criptográfica padrão da indústria com salt (como `bcryptjs` ou o módulo nativo `crypto.scryptSync`/`pbkdf2`), e eliminar fallbacks de senhas triviais hardcoded.

### [HIGH] Unsafe Deletion & Broken Referential Integrity
File: src/AppManager.js:131-137
Description: O endpoint `DELETE /api/users/:id` executa a exclusão de um registro na tabela `users` sem verificar registros vinculados, sem executar exclusão em cascata e sem envolver a operação em transação atômica. Como explicitado no próprio retorno da rota, as tabelas dependentes `enrollments` e `payments` tornam-se registros órfãos no banco de dados.
Impact: Quebra da integridade relacional do banco de dados, corrompendo consultas de histórico financeiro e gerando anomalias estruturais e dados inconsistentes.
Recommendation: Implementar integridade referencial nas foreign keys ou criar um método transacional no Model/Service que execute a remoção coordenada (ou cascata) de pagamentos, matrículas e usuário, ou implementar soft-delete.

### [HIGH] Uncontrolled Mutable Global State
File: src/utils.js:9-15
Description: O módulo exporta variáveis globais mutáveis no escopo da aplicação (`let globalCache = {}; let totalRevenue = 0;`), e a função `logAndCache` manipula diretamente esse estado global compartilhado durante requisições de checkout (`src/AppManager.js:59`).
Impact: Risco crítico de condições de corrida (race conditions) em requisições simultâneas, vazamento contínuo de memória por acúmulo ilimitado no objeto de cache em memória e comportamento não determinístico entre diferentes requisições.
Recommendation: Eliminar variáveis globais mutáveis de escopo de módulo. Utilizar injeção de dependência e serviços com escopo delimitado, ou serviços de cache estruturados (como Redis ou cache LRU com expiração e tamanho limitado).

### [MEDIUM] N+1 Query Problem & Deeply Nested Asynchronous Callbacks (Callback Hell)
File: src/AppManager.js:80-128
Description: No endpoint `GET /api/admin/financial-report`, a aplicação busca todos os cursos e, para cada curso em um loop assíncrono, executa uma nova consulta em `enrollments`. Para cada matrícula encontrada, dispara mais duas consultas sequenciais individuais (`users` e `payments`). O fluxo depende de contadores manuais (`coursesPending`, `enrPending`) para tentar sincronizar os callbacks.
Impact: Degradação severa de desempenho conforme a base de dados cresce (complexidade de queries O(C × E)), explosão de acessos concorrentes ao banco e alto risco de respostas travadas ou vazamentos assíncronos se um dos callbacks falhar.
Recommendation: Reescrever a consulta consolidando os dados em uma única query SQL relacional otimizada usando `LEFT JOIN` entre `courses`, `enrollments`, `users` e `payments`, e adotar `async/await` com Promises.

### [MEDIUM] Inconsistent Error Handling & Hardcoded Plaintext Error Responses
File: src/AppManager.js:35-71
Description: Falhas em consultas SQL e regras de negócio retornam respostas em texto puro inconsistentes com código 500 ou 400 (`"Bad Request"`, `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`, `"Erro ao criar usuário"`), sem formato JSON padronizado, sem detalhamento ou logging dos erros reais gerados pelo driver SQLite, e sem middleware de erro global.
Impact: Inconsistência nos contratos de API para os clientes consumidores, impossibilidade de diagnóstico de falhas em produção (falta de rastreabilidade de exceções) e ausência de tolerância a falhas.
Recommendation: Implementar um middleware centralizado de tratamento de erros no Express, padronizar o payload JSON de erro (`{ "error": "...", "message": "..." }`) e garantir logs estruturados das exceções capturadas.

### [LOW] Deprecated Async Callback Pattern & Lack of Modern Async/Await
File: src/AppManager.js:28-137
Description: Toda a camada assíncrona do Express é implementada com callbacks aninhados legados, sem uso de Promises modernas ou da sintaxe `async/await`, nem propagação de erros via `next(err)`.
Impact: Dificuldade de leitura, aumento da complexidade ciclomática e maior propensão a exceções não tratadas (unhandled promise rejections / uncaught exceptions).
Recommendation: Promisificar o acesso ao banco SQLite ou encapsular em camada de serviço assíncrona com `async/await` e blocos `try/catch` estruturados.

### [LOW] Magic Numbers, Cryptic Variable Names & Arbitrary Hardcoded Rules
File: src/AppManager.js:29-33
Description: O endpoint de checkout faz uso de variáveis crípticas com uma ou duas letras (`u`, `e`, `p`, `cid`, `cc`) para extrair os dados do corpo da requisição, e utiliza uma regra mágica hardcoded para simulação de gateway de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"` na linha 46).
Impact: Dificuldade de legibilidade e manutenibilidade, dificultando a compreensão imediata das regras de negócio por novos desenvolvedores.
Recommendation: Desestruturar os parâmetros de request com nomes semânticos e descritivos (`username`, `email`, `password`, `courseId`, `cardNumber`), e isolar regras de gateway de pagamento em um serviço dedicado com constantes bem definidas.

================================
Total: 10 initial findings
================================

---

# Re-Auditoria Pós-Refatoração (Validação Fase 2)

================================
ARCHITECTURE AUDIT REPORT (POST-REFACTOR)
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express (^4.18.2) + SQLite3 (^5.1.6) (MVC Architecture)
Files:   14 analyzed | ~420 lines of code

## Summary
CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 0

## Findings Status & Verification

1. [CRITICAL] Exposed Hardcoded Sensitive Credentials & Unmasked Credit Card Logging (SEC-002)
   Status: RESOLVIDO
   Evidência: Chaves de API, senhas e portas foram extraídas para variáveis de ambiente via `src/config/config.js` com fallbacks seguros e arquivo de exemplo `.env.example`. Mascaramento de cartão de crédito implementado em `src/utils/security.js:maskCardNumber` garantindo conformidade com PCI-DSS ao imprimir no log apenas os últimos 4 dígitos (`**** **** **** 4444`).

2. [CRITICAL] Monolithic God Class / God File (ARCH-001)
   Status: RESOLVIDO
   Evidência: A classe monolítica `AppManager.js` foi completamente decomposta na arquitetura MVC em camadas modulares: `src/config/`, `src/models/`, `src/controllers/`, `src/routes/` e `src/middlewares/`.

3. [HIGH] Direct Database Operations in Controllers/Routes (ARCH-002)
   Status: RESOLVIDO
   Evidência: As operações SQL foram totalmente isoladas nos modelos `src/models/userModel.js`, `src/models/courseModel.js` e `src/models/paymentModel.js`. Os controladores (`checkoutController.js`, `reportController.js`, `userController.js`) atuam exclusivamente na orquestração de requisição/resposta HTTP.

4. [HIGH] Broken Cryptography & Weak Insecure Password Hashing (SEC-003)
   Status: RESOLVIDO
   Evidência: A função insegura `badCrypto()` foi substituída pela implementação robusta com algoritmo criptográfico padrão PBKDF2 com Salt aleatório de 16 bytes e 10.000 iterações em `src/utils/security.js:hashPassword`. As senhas dos seeds e novos usuários agora utilizam este hash.

5. [HIGH] Unsafe Deletion & Broken Referential Integrity (DATA-001)
   Status: RESOLVIDO
   Evidência: Em `src/models/database.js` foi habilitado `PRAGMA foreign_keys = ON;` com `ON DELETE CASCADE`. Adicionalmente, `UserModel.deleteById()` executa a limpeza coordenada de pagamentos vinculados às matrículas antes de deletar as matrículas e o usuário, impedindo registros órfãos.

6. [HIGH] Uncontrolled Mutable Global State (ARCH-003)
   Status: RESOLVIDO
   Evidência: As variáveis globais mutáveis `globalCache` e `totalRevenue` foram eliminadas de `src/utils.js`. O estado do banco de dados é instanciado e gerenciado de forma segura via módulo `src/models/database.js`.

7. [MEDIUM] N+1 Query Problem & Deeply Nested Asynchronous Callbacks (PERF-001)
   Status: RESOLVIDO
   Evidência: A cascata de consultas aninhadas em loop assíncrono no endpoint `/api/admin/financial-report` foi substituída em `PaymentModel.getFinancialReport()` por 1 única query SQL consolidada via `LEFT JOIN` entre cursos, matrículas, usuários e pagamentos, com agregação eficiente em memória.

8. [MEDIUM] Inconsistent Error Handling & Hardcoded Plaintext Error Responses (CODE-002)
   Status: RESOLVIDO
   Evidência: Criado o middleware global `src/middlewares/errorHandler.js` registrado no Express, que captura erros assíncronos via `next(err)` e padroniza as respostas de erro JSON sem vazar stacktraces internos em ambiente de produção.

9. [LOW] Deprecated Async Callback Pattern & Lack of Modern Async/Await (DEP-001)
   Status: RESOLVIDO
   Evidência: O acesso ao SQLite foi promisificado em `src/models/database.js`. Todos os controladores e modelos foram convertidos para a sintaxe moderna `async/await` com tratamento de exceções via blocos `try/catch`.

10. [LOW] Magic Numbers, Cryptic Variable Names & Arbitrary Hardcoded Rules (CODE-004)
    Status: RESOLVIDO
    Evidência: Parâmetros crípticos foram substituídos por variáveis semânticas (`username`, `email`, `password`, `courseId`, `cardNumber`) com suporte a retrocompatibilidade. As regras de validação foram centralizadas nos controladores e models.

================================
Total: 0 remaining findings
================================
