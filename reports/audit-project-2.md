```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (CommonJS) — Node.js v20.20.2 (nenhum `engines` declarado)
Framework:     Express 4.18.2 (resolvido 4.22.1)
Dependencies:  sqlite3 5.1.6 (resolvido 5.1.7, API de callback)
Domain:        LMS / plataforma de cursos — checkout com matrícula, pagamento, auditoria e
               relatório financeiro administrativo
Architecture:  God Class. `src/AppManager.js` (141 linhas) concentra conexão de banco, DDL,
               seed, registro de rotas, regra de checkout, processamento de pagamento,
               matrícula e auditoria. `src/app.js` é só bootstrap (14 linhas) e `src/utils.js`
               mistura configuração com credenciais, cache global e criptografia caseira.
               Não existem camadas: nem config, nem model/repository, nem controller, nem
               middleware.
Source files:  3 files analyzed | ~180 lines of code
Entry point:   src/app.js:12 (`app.listen(config.port)`; `npm start` → `node src/app.js`)
Routes:        3 endpoints (AppManager.js:28, 80, 131)
DB tables:     users, courses, enrollments, payments, audit_logs (DDL em AppManager.js:12-16,
               banco `:memory:` — recriado a cada boot)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
```

Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-07-24

## Summary

CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 5

| Camada MVC | Situação |
|---|---|
| Config | **Ausente** — `src/utils.js:1-7` é um objeto literal com credenciais de produção |
| Models | **Ausente** — SQL cru dentro dos callbacks de rota (11 ocorrências) |
| Views/Routes | **Ausente** — rotas registradas dentro de um método da God Class |
| Controllers | **Ausente** — o handler de rota é o controller, o model e o service |
| Middlewares | **Ausente** — nenhum error handler, nenhuma autenticação |
| Entry point | Existe e é enxuto (`src/app.js`), mas delega tudo à God Class |

## Findings

### 1. [CRITICAL] God Class — AppManager acumula 7 responsabilidades (AP-01, AP-08)
File: src/AppManager.js:4-141
Description: Uma classe com conexão de banco no construtor (linha 7), DDL de 5 tabelas
             (12-16), seed (18-21), registro de rotas (25-138), regra de checkout (28-78),
             simulação de pagamento (45-48), matrícula (50-53), auditoria (57) e escrita em
             cache global (59).
Impact: Nenhuma dessas responsabilidades pode ser testada ou substituída isoladamente — não
        há como testar a regra de pagamento sem levantar Express e SQLite. Qualquer mudança
        no schema, na rota ou no pagamento edita o mesmo arquivo.
Recommendation: Separar em `database/` (conexão + schema), `models/*.repository.js`,
                `services/checkout.service.js`, `controllers/`, `routes/` e `middlewares/` —
                padrão RP-01.

### 2. [CRITICAL] Credenciais de Produção Hardcoded (AP-02)
File: src/utils.js:1-7, src/AppManager.js:18
Description: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey:
             "pk_live_1234567890abcdef"` e `smtpUser` literais no objeto `config`
             (utils.js:2-5); usuário de seed com senha em texto plano `'123'`
             (AppManager.js:18).
Impact: Chave `pk_live` de gateway de pagamento versionada no repositório — comprometida por
        definição, exige rotação imediata. O prefixo `pk_live` indica credencial de ambiente
        real, não de teste.
Recommendation: `src/config/index.js` lendo `process.env` com falha explícita no boot quando
                faltar variável obrigatória, `.env.example` versionado sem valores — padrão RP-02.

### 3. [CRITICAL] Dados de Cartão de Crédito e Chave do Gateway em Log (AP-19 agravado, AP-03)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
             imprime o número completo do cartão recebido e a chave do gateway.
Impact: Confirmado no baseline — o log do servidor registrou
        `Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef` para cada
        checkout. PAN completo em texto claro em log é violação direta de PCI-DSS, com
        exposição a qualquer sistema de coleta de log.
Recommendation: Remover o dado sensível do log (no máximo os 4 últimos dígitos) e usar logger
                com nível configurável — padrão RP-12.

### 4. [CRITICAL] Criptografia de Senha Caseira e Senha Default (AP-05)
File: src/utils.js:17-23, src/AppManager.js:68
Description: `badCrypto` concatena base64 do mesmo valor em laço de 10.000 iterações e
             devolve os 10 primeiros caracteres (utils.js:19-22) — sem salt, sem KDF, e o
             resultado depende apenas dos 2 primeiros caracteres do base64 da senha, ou seja,
             colide massivamente. Quando o cliente não envia senha, o sistema cria a conta
             com `"123456"` (AppManager.js:68).
Impact: Contas criadas com credencial previsível e hashes sem valor criptográfico — reverter é
        trivial por tabela de correspondência. Autenticação do sistema é inexistente na prática.
Recommendation: `bcrypt` (ou argon2) com custo configurável; recusar cadastro sem senha com
                400 em vez de aplicar default — padrão RP-04.

### 5. [HIGH] Checkout em Callback Hell sem Transação nem Rollback (AP-12, AP-10)
File: src/AppManager.js:28-78
Description: Cadeia de 5 níveis de callback: `courses` → `users` → [insert user] → insert
             `enrollments` (50) → insert `payments` (54) → insert `audit_logs` (57). Cada
             nível trata erro de forma diferente e não existe `BEGIN`/`ROLLBACK` em nenhum
             ponto do projeto.
Impact: Se o insert de `payments` falha (linha 55), a matrícula já foi persistida (linha 50) e
        o cliente recebe 500 — matrícula fantasma sem pagamento correspondente, em fluxo
        financeiro. O aninhamento torna esse caminho invisível na leitura.
Recommendation: Promisificar o driver na camada de repository, extrair `CheckoutService` com
                fluxo linear `async/await` e envolver a operação em transação com rollback —
                padrão RP-09, RP-07.

### 6. [HIGH] Estado Global Mutável Compartilhado entre Requisições (AP-09)
File: src/utils.js:9-10, 12-15, 25; src/AppManager.js:59
Description: `globalCache = {}` e `totalRevenue = 0` são variáveis de módulo mutáveis;
             `logAndCache` escreve no cache (utils.js:13-14) e é chamada no checkout
             (AppManager.js:59). `totalRevenue` é exportado por valor (utils.js:25) e nunca
             atualizado — bug latente disfarçado de funcionalidade.
Impact: Cache sem TTL nem limite cresce indefinidamente (vazamento de memória) e não sobrevive
        a múltiplas instâncias; o estado impede injeção de dependência e teste isolado.
Recommendation: Instanciar o cache no composition root e injetá-lo no service; remover o
                export morto de `totalRevenue` — padrão RP-06, RP-16.

### 7. [HIGH] Ausência de Camada de Dados — SQL Cru nos Handlers HTTP (AP-08)
File: src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133
Description: 11 queries executadas diretamente dentro de callbacks de rota, misturadas ao
             tratamento de request/response. O schema fica espalhado por handlers.
Impact: Mudança de schema exige varrer os handlers; nenhuma query é reutilizável ou testável
        sem servidor HTTP.
Recommendation: Um repository por agregado (`user`, `course`, `enrollment`, `payment`,
                `audit`) expondo métodos de domínio — padrão RP-01, RP-03.

### 8. [HIGH] Deleção que Ignora Erro e Deixa Registros Órfãos por Design (AP-10, AP-15)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` recebe `err` no callback e não o verifica (linha 133); a
             resposta 200 declara textualmente: *"Usuário deletado, mas as matrículas e
             pagamentos ficaram sujos no banco"*. Não há cascade no schema (AppManager.js:14-15)
             nem transação.
Impact: Confirmado no baseline — após `DELETE /api/users/1`, o relatório financeiro continua
        listando a matrícula e o pagamento do usuário removido, agora com `student: "Unknown"`.
        Integridade referencial quebrada em cascata, e a falha é mascarada como sucesso.
Recommendation: `ON DELETE CASCADE` no schema (ou remoção explícita dos dependentes na mesma
                transação) e propagação do erro via `next(err)` — padrão RP-07, RP-08.

### 9. [HIGH] Rota Administrativa e Deleção sem Autenticação (AP-06)
File: src/AppManager.js:80, 131
Description: `GET /api/admin/financial-report` devolve receita por curso, nome e e-mail de
             todos os alunos, sem qualquer verificação. `DELETE /api/users/:id` remove usuário
             sem autenticação. Busca por `passport|jwt|authenticate|authorization` no projeto
             não retorna nenhuma ocorrência — não existe autenticação em nenhuma rota.
Impact: Confirmado no baseline: `GET /api/admin/financial-report` → 200 com dados financeiros e
        PII, sem credencial. Qualquer cliente na rede lê o faturamento e apaga usuários.
Recommendation: Middleware `requireRole('admin')` nas rotas administrativas, negando por
                default; autenticação verificável para as rotas de escrita — padrão RP-14.

### 10. [MEDIUM] N+1 Queries com Controle Manual de Concorrência no Relatório (AP-14)
File: src/AppManager.js:83-128
Description: 1 query de cursos (83), 1 query de matrículas por curso (92), e 2 queries por
             matrícula — usuário (104) e pagamento (106). O término é controlado por
             contadores decrementados à mão (`coursesPending`, `enrPending`, linhas 86, 93,
             97-98, 117-121).
Impact: Com 20 cursos × 30 matrículas o relatório dispara ~1.221 queries. Pior: os erros em
        92, 104 e 106 são ignorados, então uma falha de query trava a resposta (contador nunca
        chega a zero) ou permite dupla chamada de `res.json`.
Recommendation: Uma query com `JOIN` + `GROUP BY` no repository de relatórios, com
                `async/await` — padrão RP-10, RP-09.

### 11. [MEDIUM] Tratamento de Erro Inconsistente e sem Middleware (AP-15)
File: src/AppManager.js:38, 41, 51, 55, 70, 84 (respondem texto puro); 92, 104, 106, 133 (ignoram o erro)
Description: Seis pontos respondem `res.status(...).send("texto em português")` numa API JSON;
             quatro recebem `err` e não o tratam. Não há `app.use((err, req, res, next) => ...)`
             no projeto.
Impact: Contrato de erro imprevisível — o cliente recebe às vezes JSON, às vezes texto puro;
        falha de banco pode resultar em requisição pendurada.
Recommendation: Classes de erro de domínio, `next(err)` nos controllers e um error middleware
                registrado por último — padrão RP-08.

### 12. [MEDIUM] Contrato de API Cifrado e sem Validação de Formato (AP-18, AP-21)
File: src/AppManager.js:29-35
Description: O payload usa `usr`, `eml`, `pwd`, `c_id`, `card`, atribuídos a variáveis `u`,
             `e`, `p`, `cid`, `cc`. A única checagem é presença (linha 35) — não há validação
             de formato de e-mail, tipo de `c_id` ou formato/luhn do cartão. `pwd` ausente é
             silenciosamente substituído por default (linha 68).
Impact: Entrada inválida chega ao banco; `cc.startsWith` (linha 46) quebra com 500 se `card`
        vier como número em vez de string.
Recommendation: Validador dedicado com nomes de domínio no contrato (`name`, `email`,
                `courseId`, `card`), validando tipo e formato — padrão RP-11, RP-13.

### 13. [MEDIUM] Schema, Seed e Escolha de Banco Embutidos na Aplicação (AP-11, AP-01)
File: src/AppManager.js:7, 10-23
Description: `new sqlite3.Database(':memory:')` fixo no construtor (linha 7); DDL e INSERTs de
             demonstração no método `initDb` (10-23), executados a cada boot.
Impact: Todo dado é perdido no restart e não há caminho de migração nem de configuração por
        ambiente — impossível apontar para um banco real sem editar código.
Recommendation: Caminho do banco por configuração, DDL em `database/schema.sql` e seed em
                script separado, executado sob demanda — padrão RP-02, RP-06.

### 14. [LOW] Regra de Aprovação de Pagamento como Número Mágico (AP-20)
File: src/AppManager.js:46
Description: `let status = cc.startsWith("4") ? "PAID" : "DENIED"` — a aprovação depende do
             primeiro dígito do cartão, sem constante nomeada nem gateway real.
Impact: Regra de negócio financeira escondida em um literal; ninguém que lê a rota entende que
        "4" significa "bandeira aceita no simulador".
Recommendation: Extrair para um `PaymentGateway` injetável (implementação fake em dev) com a
                condição nomeada — padrão RP-13, RP-01.

### 15. [LOW] `let self = this` Convivendo com Arrow Functions (AP-12, AP-21)
File: src/AppManager.js:26, 50, 54, 57
Description: `const self = this` na linha 26 é usado nos callbacks `function(err)` das linhas
             50 e 54, enquanto os demais níveis usam arrow function e `this` diretamente —
             duas estratégias de binding no mesmo método.
Impact: Leitura confusa e risco de `this` indefinido ao mover código entre os níveis.
Recommendation: `async/await` elimina a necessidade de qualquer das duas — padrão RP-09.

### 16. [LOW] Código Morto e Export Inútil (AP-22)
File: src/utils.js:10, 25; src/AppManager.js:2, 31
Description: `totalRevenue` é declarado (utils.js:10), exportado (25), importado
             (AppManager.js:2) e nunca usado nem atualizado. `globalCache` é exportado mas
             consumido apenas internamente. `let p` (linha 31) existe só para alimentar
             `badCrypto`.
Impact: Sugere funcionalidade de receita que não existe; ruído que induz o leitor a erro.
Recommendation: Remover declarações e exports não usados — padrão RP-16.

### 17. [LOW] Laço de 10.000 Iterações sem Propósito (AP-22)
File: src/utils.js:19-21
Description: O laço concatena 10.000 vezes o mesmo prefixo base64 e o resultado é truncado em
             10 caracteres — 9.995 iterações são descartadas.
Impact: Custo de CPU por cadastro sem qualquer ganho de segurança; a percepção de "hash caro"
        é falsa.
Recommendation: Substituir por `bcrypt.hash` com fator de custo real — padrão RP-04, RP-16.

### 18. [LOW] Configuração de Runtime Misturada a Segredos e Log de Boot Informal (AP-02, AP-21)
File: src/utils.js:6, src/app.js:13
Description: `port: 3000` fica dentro do mesmo objeto que guarda senha de banco e chave de
             gateway (utils.js:1-7); o boot loga `"Frankenstein LMS rodando na porta 3000..."`.
Impact: Configuração não sensível e segredo tratados com o mesmo ciclo de vida, dificultando
        aplicar controle de acesso a segredo; mensagem de boot não identifica o serviço de
        forma útil em produção.
Recommendation: Separar config pública de segredo, ambos vindos do ambiente; log de boot com
                nome do serviço, versão e porta efetiva — padrão RP-02, RP-12.

## Deprecated APIs

Verificação executada: (a) busca pelos símbolos deprecated de Node/Express do catálogo
(`new Buffer(`, `url.parse(`, `util.isArray`, `body-parser`, `crypto.createCipher`,
`fs.exists`, `app.del(`, `res.send(status, body)`, `var`); (b) carga dos módulos com
`node --pending-deprecation --throw-deprecation`; (c) `npm outdated`.

| API | Arquivo:linha | Substituto | Removida em |
|---|---|---|---|
| — | — | — | — |

Nenhuma API deprecated em uso: o projeto já usa `express.json()` (não `body-parser`),
`Buffer.from` (não `new Buffer`) e `let/const` (nenhum `var`). A carga dos módulos com avisos
de depreciação habilitados não emitiu nenhum aviso.

Contexto de versões (não são findings de API deprecated, mas de manutenção):

| Pacote | Instalado | Último major |
|---|---|---|
| express | 4.22.1 | 5.2.1 |
| sqlite3 | 5.1.7 | 6.0.1 |

## Endpoints inventariados (baseline da Fase 3)

| Método | Rota | Handler | Observação |
|---|---|---|---|
| POST | /api/checkout | AppManager.js:28 | callback hell, sem transação, PAN em log (findings 3, 5) |
| GET | /api/admin/financial-report | AppManager.js:80 | sem auth, N+1 (findings 9, 10) |
| DELETE | /api/users/:id | AppManager.js:131 | sem auth, deixa órfãos (findings 8, 9) |

Baseline capturado: 8 chamadas cobrindo os 3 endpoints (checkout de usuário novo e existente,
pagamento recusado, payload incompleto, curso inexistente, relatório antes e depois da
deleção). Resultado em `reports/validation-project-2.md`.

```
================================
Total: 18 findings
================================
```
