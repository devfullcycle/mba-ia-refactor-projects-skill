# Análise de Codebase — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 1 — Análise).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
> Reexecução da Etapa 7: a análise abaixo descreve o codebase **original** (entrada da skill) e permanece válida como contrato de referência. O estado refatorado e as correções do feedback estão em `reports/refactor-ecommerce-api-legacy.md` e `reports/validation-ecommerce-api-legacy.md`.

## 1. Resumo

| Campo | Valor |
|---|---|
| Linguagem | JavaScript (CommonJS) sobre Node.js — runtime local v24.13.0 |
| Framework | Express 4.22.1 (declarado `^4.18.2`; lock resolve 4.22.1) |
| Dependências | `express@^4.18.2`, `sqlite3@^5.1.6` (lock: 4.22.1 / 5.1.7) |
| Banco de dados | Relacional — SQLite em memória (`:memory:`), schema inline |
| Domínio | LMS / e-commerce educacional — usuários, cursos, matrículas, pagamentos, logs de auditoria |
| Arquitetura | Flat / monolito desestruturado — 3 arquivos em `src/`, sem camadas; rotas, SQL, negócio e schema no mesmo arquivo |
| Entrypoint | `src/app.js` (`package.json:5,7`) |
| Tamanho | 3 arquivos JS, 180 LOC (exclui `package-lock.json`) |
| Testes | Nenhum (sem framework, sem pasta de testes) |
| Configuração | Hardcoded em `src/utils.js:1-7`; sem `.env` |
| CI/CD / Container | Ausentes (sem `.github/`, `Dockerfile`, `docker-compose.yml`, `Makefile`) |

## 2. Evidências de detecção

### 2.1 Linguagem
- Manifest: `package.json:1-12` — name `desafio-arquitetura-ia-boilerplate`, `main: src/app.js`, script `start: node src/app.js`.
- Extensões: `.js` 3 (em `src/`), `.json` 2 (`package.json`, `package-lock.json`), `.md` 1, `.http` 1.
- Sem `tsconfig.json`, sem transpilador; uso de `require`/`module.exports` (CommonJS) em `src/app.js:1-3` e `src/AppManager.js:141`.
- **Veredito:** JavaScript (Node.js) — confiança: **alta** (manifesto + código confirmam).

### 2.2 Framework
- Dependências candidatas: `express` (`package.json:10`), `sqlite3` (`package.json:11`).
- Confirmado no código: `src/app.js:1` — `const express = require('express');`; `src/app.js:5-6` — `const app = express(); app.use(express.json());`; rotas em `src/AppManager.js:28,80,131`.
- Runtime: Node.js v24.13.0 (executado no ambiente), sem `engines` declarado no manifesto.
- **Veredito:** Express 4.22.1 (declarado `^4.18.2`; versão resolvida no `package-lock.json`) — confiança: **alta** (declarado e usado).

### 2.3 Banco de dados
- Driver/ORM: `sqlite3` (`package.json:11`), sem ORM.
- Conexão: `src/AppManager.js:7` — `this.db = new sqlite3.Database(':memory:')`.
- Schema: `CREATE TABLE` inline em `src/AppManager.js:12-16`; seeds em `:18-21`. Não há pasta de migrations nem arquivos `.sql`.
- **Veredito:** Relacional — SQLite em memória (`:memory:`), schema não versionado. Confiança: **alta**.

### 2.4 Domínio
- Rotas detectadas:
  - `POST /api/checkout` — `src/AppManager.js:28`
  - `GET /api/admin/financial-report` — `src/AppManager.js:80`
  - `DELETE /api/users/:id` — `src/AppManager.js:131`
- Entidades (tabelas): `users`, `courses`, `enrollments`, `payments`, `audit_logs` — `src/AppManager.js:12-16`.
- Recursos de negócio: checkout de curso com "pagamento" por prefixo do cartão (`:46`), matrícula (`:50`), registro de pagamento (`:54`), log de auditoria (`:57`), relatório financeiro agregado (`:80-129`), exclusão de usuário (`:131-137`).
- **Veredito:** API de LMS (Learning Management System) com fluxo de checkout e relatório financeiro administrativo — apesar do nome do diretório `ecommerce-api-legacy`. Confiança: **alta**.

## 3. Inventário

```
ecommerce-api-legacy/
├── api.http
├── package.json
├── package-lock.json
├── README.md
├── reports/
│   └── analysis-ecommerce-api-legacy.md   (este relatório)
└── src/
    ├── app.js          (14 LOC)  entrypoint / bootstrap
    ├── AppManager.js   (141 LOC) schema + rotas + negócio + SQL
    └── utils.js        (25 LOC)  config hardcoded + estado global + "crypto"
```

| Linguagem | Arquivos | LOC |
|---|---|---|
| JavaScript | 3 | 180 |
| JSON (manifest/lock) | 2 | 2.312 |
| Markdown / HTTP | 2 | 45 |

> `.claude/` contém apenas as skills do desafio e não é código da aplicação.

## 4. Arquitetura

### 4.1 Classificação
**Rótulo:** Flat / Monolítico desestruturado.

**Justificativa:** Todos os arquivos de código estão diretamente em `src/`, sem diretórios de camada (não há `controllers/`, `models/`, `services/`, `repositories/`). A classe `AppManager` (`src/AppManager.js:4-139`) acumula criação de schema, seed, definição de rotas, regra de negócio de checkout, acesso a dados e composição de relatório. O único módulo auxiliar (`src/utils.js`) mistura configuração hardcoded, cache global mutável e criptografia caseira.

### 4.2 Tabela de camadas

| Camada candidata | Diretório/arquivo | Existe? | Veredito |
|---|---|---|---|
| Model | `src/AppManager.js` (entidades SQL) | parcial | `papel violado` — entidades existem apenas como DDL inline (`:12-16`), sem classes/domínio |
| Controller/Router | `src/AppManager.js` (`setupRoutes`, `:25-138`) | sim | `papel violado` — roteia, valida, aplica negócio e executa SQL no mesmo escopo |
| View | — | não | `ausente` — API responde JSON/texto direto do handler |
| Service | — | não | `ausente` — regra de negócio vive nos callbacks das rotas |
| Data access | `src/AppManager.js` (`initDb` + queries `:10-137`) | parcial | `papel violado` — SQL disperso, sem repositório/DAO, com queries aninhadas |
| Config | `src/utils.js:1-7` | sim | `parcial` — objeto `config` centralizado, mas com segredos e porta hardcoded, sem env |
| Middleware | `src/app.js:6` | mínimo | `decorativa` — apenas `express.json()`; sem middleware de erro, auth ou logging |
| Utils | `src/utils.js` | sim | `papel violado` — estado global mutável (`:9-10`), cache (`:12-15`), hash caseiro (`:17-23`) |
| Tests | — | não | `ausente` |
| Migrations | — | não | `ausente` — schema criado no boot em memória |

Legenda do veredito: `adequada` | `parcial` | `papel violado` | `ausente` | `decorativa`.

### 4.3 Leitura dos arquivos-chave

| Arquivo | LOC | Papel real | Observações |
|---|---|---|---|
| `src/app.js` | 14 | Bootstrap HTTP | Instancia Express, registra `express.json()`, cria `AppManager`, chama `initDb()` e `setupRoutes()`, sobe na porta 3000. Não há error handler nem shutdown/close do DB. |
| `src/AppManager.js` | 141 | Schema + rotas + negócio + acesso a dados | Classe única com responsabilidades acumuladas. Checkout usa callbacks aninhados (piramide), cria usuário se não existir e decide pagamento por prefixo do cartão. Relatório faz loops com queries internas (N+1). Delete ignora erro e não limpa dependências. |
| `src/utils.js` | 25 | Config + estado global + crypto | `config` com usuário/senha de DB, chave de gateway e SMTP literais. `globalCache` e `totalRevenue` mutáveis em escopo de módulo. `badCrypto` repete base64 e trunca em 10 chars, sem salt. |

## 5. Entrypoints, configuração e testes

- **Entrypoints:** `src/app.js` (`package.json:5` `main`, `package.json:7` script `start`).
- **Configuração:** hardcoded em `src/utils.js:1-7` (`dbUser`, `dbPass`, `paymentGatewayKey`, `smtpUser`, `port: 3000`). Não há `.env`, `.env.example`, `config/` ou leitura de `process.env`.
- **Testes:** ausentes. Não há `tests/`, `__tests__/`, `*.test.js`, `jest`/`mocha`/`supertest` em `package.json`, nem script `test`.
- **CI/CD:** ausente (sem `.github/workflows/`, `.gitlab-ci.yml`).
- **Containerização:** ausente (sem `Dockerfile`/`docker-compose.yml`).
- **Dependências instaladas no ambiente:** `node_modules/` não existe; versões acima vêm do `package-lock.json` (lockfileVersion 3).

## 6. Candidatos a anti-pattern

Achados que a própria leitura de código já revelou. **Não** são o relatório de auditoria — a Fase 2 confirma, classifica severidade e localiza linha exata.

| # | Sinal observado | Evidência | Anti-pattern candidato |
|---|---|---|---|
| 1 | Credenciais e chave de gateway literais no código | `src/utils.js:1-7` | Credencial hardcoded |
| 2 | Número completo do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Exposição de dado sensível (PII/PCI) em log |
| 3 | Hash de senha caseiro (base64 repetido + truncamento), sem salt | `src/utils.js:17-23` | Criptografia fraca |
| 4 | Senha seed armazenada em texto puro | `src/AppManager.js:18` | Senha em texto puro |
| 5 | Estado global mutável exportado | `src/utils.js:9-10,25` | Estado global mutável |
| 6 | `totalRevenue` importado e nunca usado | `src/AppManager.js:2`; `src/utils.js:10` | Dependência/código morto |
| 7 | Classe única com schema, rotas, negócio, pagamento e relatório | `src/AppManager.js:4-139` | God Class |
| 8 | Regra de negócio de pagamento/matrícula dentro do handler HTTP | `src/AppManager.js:43-64` | Lógica de negócio no Controller |
| 9 | Loops de cursos → matrículas com query por usuário e por pagamento | `src/AppManager.js:89-127` | N+1 queries |
| 10 | Validação restrita a presença de campos; email/cartão/id não validados | `src/AppManager.js:35` | Validação de entrada ausente |
| 11 | `DELETE` ignora `err` e sempre responde sucesso, deixando órfãos | `src/AppManager.js:131-136` | Tratamento de erro genérico / integridade referencial |
| 12 | Erros de query não checados no relatório e no audit log | `src/AppManager.js:57,83,92,104,106` | Erro engolido / ausência de tratamento |
| 13 | Escritas de checkout sem transação (matrícula/pagamento/audit) | `src/AppManager.js:50-63` | Ausência de transação / escrita parcial |
| 14 | Endpoint administrativo de relatório sem autenticação/autorização | `src/AppManager.js:80` | Broken access control |
| 15 | DDL e seeds embutidos no boot, sem migrations | `src/AppManager.js:10-23` | Schema sem versionamento |
| 16 | Callbacks profundamente aninhados no checkout e relatório | `src/AppManager.js:37-77,83-128` | Callback hell / baixa testabilidade |
| 17 | Nomes abreviados (`u`, `e`, `p`, `cid`, `cc`) e regra mágica `startsWith("4")` | `src/AppManager.js:29-33,46` | Baixa legibilidade / magic value |
| 18 | Banco sempre em memória, sem persistência ou close explícito | `src/AppManager.js:7` | Configuração de banco inadequada para produção |
| 19 | Ausência total de testes automatizados | `package.json:6-8` | Cobertura de testes ausente |
| 20 | Ausência de middleware central de erros e de rota 404 | `src/app.js:5-14` | Tratamento de erro não centralizado |

## 7. Notas e lacunas

- O nome do diretório sugere e-commerce genérico, mas o código implementa um **LMS** (cursos/matrículas); o domínio foi inferido das entidades e rotas, não do nome.
- Versões de `express` e `sqlite3` vêm do `package-lock.json`; não foi executado `npm install`, portanto não há confirmação de runtime instalado no projeto.
- Não foi possível determinar regras de negócio pretendidas (ex.: critério real de aprovação de pagamento) — o código simula aprovação pelo primeiro dígito do cartão (`src/AppManager.js:46`).
- Sem testes, não há contrato comportamental formal; o inventário de rotas acima é a única referência de contrato para as próximas fases.
- Não há migrations, então o schema efêmero em memória não representa um banco de produção.
- Referências da skill cobrem o ecossistema Node/Express sem lacunas relevantes.
