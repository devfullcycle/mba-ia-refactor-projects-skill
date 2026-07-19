# Fase 1 — Heurísticas de Análise de Projeto

Objetivo: detectar **linguagem, framework, dependências, banco de dados, domínio e arquitetura**
lendo o projeto, sem assumir nada pelos nomes dos arquivos. Tudo aqui é agnóstico de stack — as
tabelas dão os sinais concretos para as stacks mais comuns, mas o método vale para qualquer uma.

## Método geral

1. **Comece pelos manifestos de dependências** — eles revelam linguagem, framework e libs de uma vez.
2. **Liste os arquivos-fonte** (excluindo `node_modules`, `venv`, `.venv`, `.git`, `__pycache__`, `dist`, `build`).
3. **Leia os arquivos principais de verdade**: entrypoint, definição de rotas, camada de dados.
   Nomes enganam; o conteúdo não.
4. **Mapeie a arquitetura**: quantos arquivos, como as responsabilidades estão distribuídas, se há
   separação de camadas ou tudo está junto.

## Detecção de linguagem e framework

| Sinal (arquivo) | Linguagem | Como achar o framework + versão |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | Procure `flask`, `django`, `fastapi`, `starlette` na lista de deps; a versão vem fixada (ex.: `flask==3.1.1`) |
| `package.json` | JavaScript/TypeScript (Node.js) | Campo `dependencies`: `express`, `koa`, `fastify`, `nestjs`; versão no valor (ex.: `"express": "^4.18.2"`) |
| `pom.xml`, `build.gradle` | Java | Spring/Spring Boot nas dependências |
| `go.mod` | Go | `gin`, `echo`, `fiber` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `composer.json` | PHP | `laravel`, `symfony` |

Se houver `tsconfig.json` ou arquivos `.ts`, a linguagem é TypeScript.
Registre o runtime quando for informativo (ex.: `JavaScript (Node.js)`).

## Detecção de dependências principais

- Liste apenas as **diretas** (declaradas no manifesto), **não** as transitivas.
- **Não repita o framework** (ele já tem linha própria).
- Mostre só os nomes, separados por vírgula. Foque nas que têm papel arquitetural:
  ORM (`flask-sqlalchemy`, `sequelize`, `prisma`), CORS, validação (`marshmallow`, `joi`, `zod`),
  auth, cache, cliente HTTP.

## Detecção de banco de dados

Leia a camada de dados (arquivos tipo `database.*`, `db.*`, models, ou a inicialização no entrypoint).

| Sinal no código | Engine | Forma de acesso |
|---|---|---|
| `sqlite3.connect(...)`, `require('sqlite3')` | SQLite | driver direto (SQL manual) |
| `:memory:` como caminho | SQLite **in-memory** | ⚠️ dados voláteis — some a cada restart |
| `SQLAlchemy`, `db.Model`, `flask_sqlalchemy` | (o do `SQLALCHEMY_DATABASE_URI`) | ORM |
| `sequelize`, `prisma`, `typeorm`, `mongoose` | conforme config | ORM/ODM |
| `psycopg2`, `pg`, `postgres://` | PostgreSQL | driver ou ORM |
| `mysql`, `mysql2`, `pymysql` | MySQL | driver ou ORM |

Extraia o engine, a forma de acesso e nuances relevantes. Ex.:
`SQLite in-memory (dados voláteis, driver sqlite3)` ou `SQLite via SQLAlchemy ORM (tasks.db)`.

### Tabelas do banco

Ache os nomes das tabelas por qualquer um destes caminhos:
- `CREATE TABLE <nome>` em SQL embutido.
- Classes de modelo do ORM (`class Produto(db.Model)` → tabela `produtos`/`produto`); veja
  `__tablename__` quando existir.
- Migrations ou seeds.

Liste os nomes reais das tabelas, separados por vírgula.

## Detecção de domínio

Inferir do conjunto de: nomes de tabelas/entidades, rotas e vocabulário do código.
Descreva em uma frase curta com as entidades principais. Exemplos:
- Tabelas `produtos, usuarios, pedidos, itens_pedido` → `E-commerce API (produtos, pedidos, usuários)`.
- Tabelas `users, courses, enrollments, payments` → `LMS API (cursos, matrículas, pagamentos)`.
- Tabelas `tasks, users, categories` → `Task Manager API (tarefas, usuários, categorias)`.

## Mapeamento de arquitetura (resumo em 1 linha)

Avalie como as responsabilidades estão distribuídas e resuma em uma linha. Padrões comuns:

| Situação observada | Resumo sugerido |
|---|---|
| Tudo em poucos arquivos, sem camadas | `Monolítica — tudo em N arquivos, sem separação de camadas` |
| Uma classe/arquivo central que faz tudo | `God Class — um único componente concentra DB, regras e rotas` |
| Alguma separação (models/routes) mas com lógica vazando | `Parcialmente em camadas — models/routes presentes, sem controllers` |
| MVC bem separado | `Em camadas — MVC com models, controllers e rotas separados` |

As nuances detalhadas **não** vão nesta linha — elas viram findings na Fase 2.

## Contagem de arquivos-fonte

Conte os arquivos-fonte da linguagem principal, excluindo diretórios de dependências
(`node_modules`, `venv`, `.venv`, `.git`, `__pycache__`, `dist`, `build`). Inclua scripts
auxiliares do próprio projeto (ex.: `seed.py`). Reporte como `<N> files analyzed`.

## Saída

Monte o bloco `PHASE 1: PROJECT ANALYSIS` conforme `03-report-templates.md`, **omitindo** as linhas
de campos que não se aplicam ao projeto (ex.: sem banco → sem `Database` e sem `DB tables`).
