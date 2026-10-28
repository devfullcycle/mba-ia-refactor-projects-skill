# Detecção de Stack — Linguagem, Framework, Banco de Dados

Heurísticas gerais, aplicáveis a qualquer ecossistema. Ordem: **manifesto → dependências → código → arquivos de lock/config**.

## 1. Manifestos por ecossistema

| Manifesto | Linguagem | Ecosystem | Como extrair deps |
|---|---|---|---|
| `package.json` | JavaScript / TypeScript | npm | `dependencies` + `devDependencies` |
| `tsconfig.json` | TypeScript | npm | indica TS sobre JS |
| `requirements*.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Python | pip / poetry / pipenv | listas de deps |
| `go.mod` | Go | go modules | `require` |
| `pom.xml` | Java / Kotlin | Maven | `<dependencies>` |
| `build.gradle`, `build.gradle.kts` | Java / Kotlin / Groovy | Gradle | `dependencies { }` |
| `Cargo.toml` | Rust | cargo | `[dependencies]` |
| `Gemfile` | Ruby | bundler | `gem` |
| `composer.json` | PHP | composer | `require` / `require-dev` |
| `*.csproj`, `*.fsproj` | C# / F# | NuGet | `PackageReference` |
| `pubspec.yaml` | Dart | pub | `dependencies` |
| `mix.exs` | Elixir | hex | `deps` |
| `CMakeLists.txt` | C/C++ | cmake | `find_package` / `target_link_libraries` |
| `deno.json`, `import_map.json` | TypeScript | deno | `imports` |
| `Dockerfile` (sem manifest) | inferir do `FROM` e do conteúdo | — | — |

**Sem manifesto:** conte extensões excluindo ignorados. Exemplo: `.py` 12, `.js` 3 → Python.

**Manifesto secundário** (monorepo): `lerna.json`, `nx.json`, `turbo.json`, `pnpm-workspace.yaml`, `rush.json` → o projeto é multi-pacote. Reporte o pacote raiz como entrada principal.

## 2. Dicionário de frameworks

### Python
| Dependência | Framework / papel |
|---|---|
| `flask` | Flask — microframework web |
| `django` | Django — framework full-stack (MVT) |
| `fastapi` | FastAPI — API assíncrona (Pydantic) |
| `uvicorn`, `gunicorn` | servidor ASGI/WSGI |
| `starlette` | ASGI base |
| `pyramid`, `tornado`, `bottle`, `sanic`, `aiohttp` | frameworks web alternativos |
| `sqlalchemy`, `flask-sqlalchemy` | ORM |
| `peewee`, `tortoise`, `django-orm` | ORM |
| `psycopg2`/`psycopg`, `pymysql`, `mysqlclient` | driver relacional |
| `marshmallow`, `pydantic`, `attrs`, `cerberus` | validação/serialização |
| `sqlmodel` | ORM + pydantic |
| `pytest`, `unittest` | teste |

### Node / TypeScript
| Dependência | Framework / papel |
|---|---|
| `express` | Express — middleware HTTP |
| `fastify`, `koa`, `hapi`, `restify` | frameworks alternativos |
| `@nestjs/core` | NestJS — modular/DI, opinionado |
| `next`, `nuxt`, `remix`, `svelte`, `@angular/core`, `vue` | frameworks front/full-stack |
| `mongoose`, `sequelize`, `typeorm`, `prisma`, `@prisma/client`, `knex`, `drizzle-orm`, `mikro-orm` | ORM/ODM/query-builder |
| `mysql2`, `pg`, `better-sqlite3`, `sqlite3`, `mongodb` | drivers |
| `jsonwebtoken`, `passport`, `bcrypt`, `argon2` | auth/crypto |
| `dotenv` | config por env |
| `jest`, `vitest`, `mocha`, `chai`, `supertest` | teste |
| `eslint`, `prettier`, `typescript`, `ts-node` | tooling |

### Java / Kotlin
`spring-boot-starter-web` → Spring Boot; `spring-boot-starter-data-jpa` → JPA; `quarkus` / `micronaut` → alternatives; `hibernate`; `junit-jupiter`; `jakarta.persistence`; `mapstruct`; `lombok`.

### Ruby
`rails` → Rails (MVC nativo); `sinatra` → Sinatra; `sequel`/`activerecord`; `rspec`/`minitest`.

### PHP
`laravel/framework` → Laravel; `symfony/*` → Symfony; `slim/*`; `cakephp/*`; `doctrine/orm`; `monolog`.

### Go
`gin-gonic/gin`, `gofiber/fiber`, `labstack/echo`, `gorilla/mux`; `gorm.io/gorm`; `go-redis`; `stretchr/testify`.

### Rust
`axum`, `actix-web`, `rocket`, `warp`; `diesel`, `sqlx`; `serde`; `tokio`.

### .NET
`Microsoft.AspNetCore.App` → ASP.NET Core; `Microsoft.EntityFrameworkCore` → EF Core; `AutoMapper`; `xunit`/`NUnit`.

### Dart / Flutter
`flutter` → Flutter; `provider`, `riverpod`, `bloc`; `sqflite`/`drift`; `http`.

## 3. Detecção de framework — nuances

- **Dependência ≠ uso.** Sempre confirme no código. Grep por `from flask import` / `require('express')` / `@app.route` / `app.get(` / `@RestController` / `Model` (Rails) / `DjangoModel` (Django).
- **Framework implícito:** `requirements.txt` vazio mas existe `templates/` + `manage.py` → Django. Só `app.py` com `Flask(__name__)` → Flask. `server.js` com `http.createServer` → Node puro, sem framework.
- **Runtime vs framework:** `uvicorn` é servidor, `express` é framework. Reporte separadamente.
- **Versão:** do manifesto (range como `^4.18.2`, `==3.1.1`). Versão *em runtime* só se a lib estiver instalada e você puder importá-la — não presuma.
- **Monolito vs microserviços:** presença de múltiplos `Dockerfile`, `docker-compose.yml` com vários serviços, ou vários manifests em subdiretórios indica **vários deployables**. Reporte quantos e quais.

## 4. Banco de dados

### Do manifesto
| Dependência | Tipo |
|---|---|
| `sqlite3`, `better-sqlite3`, `flask-sqlalchemy` + `sqlite:///` | Relacional — SQLite (arquivo local) |
| `psycopg2`, `psycopg`, `pg` | Relacional — PostgreSQL |
| `pymysql`, `mysql2`, `mysqlclient` | Relacional — MySQL/MariaDB |
| `oracledb`, `cx_Oracle` | Relacional — Oracle |
| `sqlalchemy`, `prisma`, `typeorm`, `sequelize`, `knex`, `drizzle`, `pewee`, `django-orm` | ORM → o DB vem da connection string |
| `mongoose`, `mongodb`, `motor` | Documento — MongoDB |
| `redis`, `ioredis` | Cache/NoSQL — Redis |
| `elasticsearch`, `meilisearch` | Search |
| `neo4j`, `sauron` | Grafo |

### Do código
Grep por strings de conexão: `sqlite:///`, `postgres://`, `postgresql://`, `mysql://`, `mongodb://`, `redis://`, `amqp://`, `Server=` (SQL Server).

### Classificação a reportar
- **Relacional** + engine específica
- **Documento/NoSQL** + engine
- **Em memória**
- **ORM presente, engine via config**
- **Não identificável** — sem driver e sem string de conexão

### Achados relacionados a reportar
- Credencial de conexão **hardcoded** em código (fase 2 → CRITICAL/HIGH)
- Schema definido em código (SQL `CREATE TABLE` inline) vs migrations versionadas
- Ausência de migrations/pasta de migrations

## 5. Integrações e infraestrutura

Grep por: `requests`, `httpx`, `axios`, `fetch(`, `smtplib`, `boto3`, `@aws-sdk`, `stripe`, `mercadopago`, `paypal`, `sendgrid`, `twilio`, `celery`, `bull`, `kafka`, `socket.io`, `redis`, `pika`.

Infra: `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, `.gitlab-ci.yml`, `Makefile`, `Procfile`, `k8s/`, `helm/`, `terraform/`, `ansible/`.

Config: `.env` / `.env.example` / `config.py` / `config/settings.py` / `src/config` → **gerência de configuração por env** vs valores hardcoded no código.

Testes: `tests/`, `__tests__/`, `spec/`, `*_test.go`, `*.test.ts`, `pytest.ini`, `jest.config.js` → framework de teste e presença de cobertura.

CI/CD: pasta de workflows + badges no README.

## 6. Como reportar

Sempre com evidência. Formato de item:

> **Linguagem:** Python 3 — evidência: `requirements.txt` (`flask==3.1.1`), 4 arquivos `.py`, entrypoint `app.py`.

Avoid:
- "provavelmente é Python" quando o manifesto é conclusivo — seja direto.
- "usa Flask" quando Flask está no requirements mas nenhum arquivo importa — "dependência declarada, uso não confirmado no código".
- Citar versão de runtime sem ter executado o interpretador.
