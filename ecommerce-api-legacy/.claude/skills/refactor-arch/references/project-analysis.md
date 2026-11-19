# Project Analysis — Heurísticas de Detecção (Fase 1)

Objetivo: descobrir **linguagem, framework, banco de dados, domínio e
arquitetura atual** a partir de evidências do próprio projeto. Nunca assuma a
stack — prove cada conclusão citando o arquivo que a sustenta.

## 1. Detecção de linguagem

Olhe primeiro o manifesto de dependências e as extensões de arquivo dominantes.

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| `package.json`, `*.js`, `*.ts`, `*.mjs` | Node.js (JS/TS) |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `go.mod`, `*.go` | Go |

Versão da linguagem: cheque `python_requires`, campo `engines` no
`package.json`, `.python-version`, `go.mod`, etc. Se não houver, reporte
"não especificada" e use a versão do runtime instalado.

## 2. Detecção de framework web

Leia o manifesto de dependências **e** os imports do entry point.

| Sinal | Framework |
|---|---|
| `flask` em deps + `Flask(__name__)` | Flask |
| `django` + `manage.py` / `settings.py` | Django |
| `fastapi` + `FastAPI()` | FastAPI |
| `express` em deps + `require('express')` / `express()` | Express |
| `@nestjs/core` | NestJS |
| `koa`, `fastify`, `hapi` | respectivo |
| `spring-boot-starter-web` | Spring Boot |

Pegue a versão no manifesto (ex.: `"express": "^4.18.2"` → Express 4.x;
`flask==3.0.0` → Flask 3.0). Liste também libs de apoio relevantes
(`flask-cors`, `flask-sqlalchemy`, `sqlite3`, `cors`, ORMs, etc.).

## 3. Detecção de banco de dados

- **Driver/ORM nas deps:** `sqlite3`, `psycopg2`, `pymysql`, `mysql2`, `pg`,
  `mongoose`, `flask-sqlalchemy`, `sequelize`, `prisma`, `typeorm`.
- **Connection strings / paths:** `sqlite:///...`, `postgres://...`,
  `mongodb://...`, `:memory:`, `*.db`.
- **Tabelas/entidades:** procure `CREATE TABLE <nome>`, classes de model
  (`class X(db.Model)`, `@Entity`, schemas Mongoose) e nomes de coleção.
  Liste os nomes reais encontrados.

## 4. Detecção de domínio

Infira o domínio de negócio a partir de:
- Nomes de **rotas/endpoints** (`/produtos`, `/checkout`, `/tasks`).
- Nomes de **tabelas/entidades** (`usuarios`, `pedidos`, `enrollments`, `tasks`).
- Mensagens, títulos e seeds no código.

Descreva em uma frase: ex. "E-commerce API (produtos, pedidos, usuários)",
"LMS com fluxo de checkout (cursos, matrículas, pagamentos)", "Task Manager
(tarefas, usuários, categorias, relatórios)".

## 5. Mapeamento da arquitetura atual

Classifique o estado atual em um dos níveis — isso define o esforço da Fase 3:

- **Monolito desestruturado:** tudo em 1–4 arquivos, sem separação de camadas;
  rotas, regras de negócio, SQL e config misturados. (ex.: God Class / God File)
- **Camadas parciais:** já existem pastas como `models/`, `routes/`,
  `services/`, mas com vazamentos (lógica de negócio na rota, serialização
  manual repetida, sem camada de controller/serviço clara, segredos no código).
- **MVC/limpo:** camadas bem separadas com responsabilidades claras (raro em
  legado — confirme com ceticismo).

Para cada camada, anote **onde** cada responsabilidade vive hoje:
roteamento, validação, regra de negócio, acesso a dados, serialização,
configuração, tratamento de erros. Essa planilha mental guia a refatoração.

## 6. Contagem de arquivos

Conte apenas arquivos-fonte da aplicação. **Ignore:** `node_modules/`,
`venv/`, `.venv/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `*.db`,
lockfiles e a própria pasta `.claude/`. Reporte o número real — ele precisa
bater com a realidade do repositório.

## Saída da fase

Preencha o bloco `PHASE 1: PROJECT ANALYSIS` do SKILL.md com os dados acima e
siga para a auditoria. Guarde a lista de endpoints detectados — ela será a
base da validação na Fase 3.
