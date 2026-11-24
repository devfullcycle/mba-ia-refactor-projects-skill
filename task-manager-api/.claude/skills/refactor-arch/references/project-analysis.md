# Análise de Projeto — Heurísticas de Detecção

Use estas heurísticas na Fase 1. Combine mais de um sinal: manifestos indicam a stack, imports confirmam o framework.

## 1. Linguagem

| Sinal (arquivo/extensão) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| `package.json`, `*.js`, `*.mjs`, `*.ts` | JavaScript / TypeScript (Node.js) |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `composer.json`, `*.php` | PHP |
| `go.mod`, `*.go` | Go |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.cs` | C# |

Se houver várias, a linguagem do **ponto de entrada** e do manifesto de dependências do backend prevalece. Em `package.json`, o campo `"type"` (`module`/`commonjs`) indica ESM vs CJS; `tsconfig.json` indica TypeScript.

## 2. Framework

Procure nas dependências do manifesto e nos imports do ponto de entrada.

| Indício | Framework |
|---|---|
| `flask`, `Flask(__name__)`, `@app.route` | Flask |
| `fastapi`, `FastAPI()`, `@app.get` | FastAPI |
| `django`, `manage.py`, `urls.py`, `settings.py` | Django |
| `express`, `app.use(`, `app.get(` / `router.get(` | Express |
| `@nestjs/*`, `@Controller` | NestJS |
| `koa`, `fastify`, `hapi` | Koa / Fastify / Hapi |
| `spring-boot-starter`, `@RestController` | Spring Boot |
| `laravel/framework`, `artisan` | Laravel |
| `gin-gonic/gin`, `labstack/echo`, `net/http` | Gin / Echo / stdlib |
| `rails` no Gemfile, `config/routes.rb` | Rails |

Registre a **versão** (manifesto/lockfile): ela é necessária para a checagem de APIs deprecated.

## 3. Banco de dados

| Indício | Banco / acesso |
|---|---|
| `sqlite3`, `better-sqlite3`, `*.db`, `*.sqlite`, `:memory:` | SQLite |
| `psycopg2`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `mysql2`, `pymysql`, `mysql://` | MySQL/MariaDB |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `redis` | Redis |
| `SQLAlchemy`, `Sequelize`, `Prisma`, `TypeORM`, `Hibernate`, `Eloquent`, `GORM`, `ActiveRecord` | ORM (informe qual) |
| Strings `SELECT/INSERT/UPDATE/DELETE` no código | SQL cru / driver direto |

Identifique também: onde a conexão é criada (global? por request?), onde o schema é criado/populado (seed no boot?), e como as queries são montadas (concatenação vs parametrizadas).

## 4. Ponto de entrada e execução

Procure: `app.py`, `main.py`, `server.js`, `index.js`, `app.js`, `Main.java`/`Application.java`, `main.go`, `public/index.php`. Confirme em scripts do manifesto (`npm start`, `scripts` no `package.json`), `Procfile`, `Dockerfile`, `Makefile` ou README. Anote o comando de execução e a porta.

## 5. Mapeamento da arquitetura atual

1. Liste todos os arquivos-fonte (ignore `node_modules`, `venv`, `.git`, `dist`, `build`, `__pycache__`).
2. Para cada arquivo, classifique a(s) camada(s) que ele mistura:
   - **Rota/Controller**: define endpoints, lê request, devolve response.
   - **Model/Dados**: acesso ao banco, queries, entidades.
   - **Serviço/Negócio**: regras, cálculos, validações.
   - **Config**: portas, segredos, flags, conexão.
   - **Util/Outros**.
3. Meça sinais de organização:
   - Nº de arquivos e linhas por arquivo (um arquivo > 300 linhas ou com 3+ camadas = "God file").
   - Existem pastas por responsabilidade (`models/`, `controllers/`, `routes/`)?
   - Rotas importam o banco diretamente?
4. Classifique o nível:
   - **Monolítico**: tudo em 1–3 arquivos, camadas misturadas.
   - **Parcial**: há separação de pastas, mas com vazamento entre camadas (SQL em controller, regra em rota).
   - **Em camadas**: estrutura MVC/similar já existe — o foco da auditoria passa a ser desvios finos, duplicação, deprecated e segurança.
5. Levante endpoints: método + caminho + arquivo/linha do handler. Esta lista é o **contrato** que a Fase 3 deve preservar.
6. Levante entidades do domínio (tabelas/coleções, classes de dados).

## 6. Dicas para projetos não-API

Se for app com templates (Django, Rails, Blade, EJS), as **Views** são os templates; mapeie-os também. Se for CLI ou worker, adapte "endpoints" para "comandos/jobs" e mantenha a mesma lógica de camadas.
