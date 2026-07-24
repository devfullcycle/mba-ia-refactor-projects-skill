# Heurísticas de Análise de Projeto (Fase 1)

Objetivo: descobrir linguagem, framework, banco, rotas e camadas **por evidência**, sem
assumir nada sobre nomes de arquivo. Toda conclusão precisa citar o arquivo que a sustenta.

## 1. Linguagem e gerenciador de pacotes

Procure o manifesto na raiz (e um nível abaixo, para monorepos):

| Arquivo encontrado | Linguagem | Notas |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `environment.yml` | Python | `pyproject.toml` pode indicar poetry/uv/hatch |
| `package.json` | JavaScript/TypeScript | `tsconfig.json` presente ⇒ TypeScript |
| `pom.xml`, `build.gradle(.kts)` | Java/Kotlin | |
| `composer.json` | PHP | |
| `go.mod` | Go | |
| `Gemfile` | Ruby | |
| `*.csproj`, `*.sln` | C#/.NET | |
| `Cargo.toml` | Rust | |

Se não houver manifesto, decida pela extensão dominante dos arquivos-fonte.

Versão da linguagem: `python_requires`/`requires-python`, `engines.node`, `<java.version>`,
`go 1.x`, `.python-version`, `.nvmrc`, `runtime.txt`, `Dockerfile`.

## 2. Framework e versão

Ordem de confiança: **manifesto pinado → lockfile → import no código → versão instalada**.

| Sinal no manifesto | Framework | Sinal confirmatório no código |
|---|---|---|
| `flask` | Flask | `from flask import Flask`, `Flask(__name__)` |
| `django` | Django | `settings.py`, `urls.py`, `manage.py` |
| `fastapi` | FastAPI | `FastAPI()`, `@app.get` |
| `express` | Express | `require('express')`, `express()`, `app.listen` |
| `@nestjs/core` | NestJS | `@Controller()`, `@Module()` |
| `koa`, `fastify`, `hapi` | idem | `new Koa()`, `fastify()` |
| `spring-boot-starter-web` | Spring Boot | `@RestController`, `@SpringBootApplication` |
| `laravel/framework` | Laravel | `routes/web.php`, `Illuminate\` |
| `symfony/*` | Symfony | `#[Route]` |
| `rails` | Rails | `config/routes.rb` |
| `gin-gonic/gin`, `labstack/echo` | Gin/Echo | `gin.Default()` |

Comandos úteis (agnósticos):

```bash
# manifestos e versões
cat requirements.txt pyproject.toml package.json pom.xml go.mod 2>/dev/null
# imports de framework
grep -rn -iE "^(import|from|const .*require|use |using )" --include='*.py' --include='*.js' --include='*.ts' . | head -50
```

Anote também as dependências **declaradas e não usadas** — vira finding LOW (código morto)
e ajuda a explicar a intenção original do autor.

## 3. Entry point

| Stack | Onde olhar |
|---|---|
| Python | `if __name__ == "__main__":`, `app.run(`, `create_app(`, `wsgi.py`, `asgi.py` |
| Node | `package.json` → `main` e `scripts.start`; `app.listen(` |
| Java | classe com `public static void main` / `@SpringBootApplication` |
| Go | `func main()` |
| PHP | `public/index.php` |

```bash
grep -rn "__main__\|app.run(\|app.listen(\|func main()\|public static void main" --include='*.*' . | grep -v node_modules
```

## 4. Inventário de rotas (base do baseline e da validação)

Liste **todas** as rotas com método, caminho e handler. Padrões por stack:

| Stack | Padrões de registro |
|---|---|
| Flask | `@app.route`, `@bp.route`, `app.add_url_rule(...)`, `register_blueprint` |
| FastAPI | `@app.get/post/put/delete`, `include_router` |
| Django | `path(`, `re_path(`, `router.register(` |
| Express | `app.get/post/put/patch/delete`, `router.<verbo>`, `app.use('/prefix', ...)` |
| NestJS | `@Get()`, `@Post()` dentro de `@Controller('prefix')` |
| Spring | `@GetMapping`, `@RequestMapping` |
| Rails/Laravel | `config/routes.rb`, `routes/*.php` |

```bash
grep -rnE "@(app|bp|router|blueprint)[a-z_]*\.(route|get|post|put|patch|delete)|add_url_rule|(app|router)\.(get|post|put|patch|delete)\(" --include='*.py' --include='*.js' --include='*.ts' . | grep -v node_modules
```

⚠️ Duas convenções de roteamento no mesmo projeto (ex.: `add_url_rule` **e** `@app.route`) já
é um finding em si — registre.

## 5. Camada de dados

**Driver / cliente:** `sqlite3`, `psycopg2`, `mysql-connector`, `pymongo`, `redis`, `pg`,
`mysql2`, `mongoose`, `better-sqlite3`.

**ORM / query builder:** SQLAlchemy (`db.Model`, `declarative_base`), Django ORM
(`models.Model`), Sequelize (`sequelize.define`, `Model.init`), Prisma (`schema.prisma`),
TypeORM (`@Entity`), Mongoose (`new Schema`), Eloquent, Hibernate (`@Entity`), GORM.

**Como levantar as tabelas/coleções:**

```bash
# DDL literal
grep -rniE "create table|create collection" --include='*.*' . | grep -v node_modules
# tabelas declaradas por ORM
grep -rnE "__tablename__|@Entity|tableName|db\.Model|models\.Model|new Schema" . | grep -v node_modules
# nomes citados em SQL cru
grep -rnoiE "(from|into|update|join)[[:space:]]+[a-z_][a-z0-9_]*" --include='*.py' --include='*.js' . | grep -v node_modules
# migrations
ls migrations/ db/migrate/ prisma/ alembic/ 2>/dev/null
```

Registre também **onde** o schema é criado. DDL executado em tempo de import ou dentro de um
getter de conexão é finding (acoplamento de infra ao runtime).

## 6. Mapeamento de camadas

Classifique **cada** arquivo-fonte em uma das camadas, pelo conteúdo — não pelo nome:

| Camada | Evidência de que o arquivo pertence a ela |
|---|---|
| Entry point / composition root | cria a aplicação, registra rotas, sobe o servidor |
| Config | lê variáveis de ambiente, expõe constantes de configuração |
| View / Routes | só mapeia caminho → handler, sem lógica |
| Controller | orquestra: recebe request, valida entrada, chama model/service, monta resposta |
| Model / Repository | acesso a dados e regras do agregado |
| Service | regra de negócio que atravessa agregados, integração externa |
| Middleware | erro, auth, log, CORS |
| Util | funções puras sem dependência de framework |

Depois monte a matriz de responsabilidades misturadas — é o insumo direto dos findings de
God Class e Fat Controller:

```
arquivo             | SQL/ORM | validação | regra de negócio | resposta HTTP | rota | config
models.py           |    ✓    |     -     |        ✓         |       ✓       |  -   |   -
```

Um arquivo com ✓ em `SQL/ORM` **e** `resposta HTTP` (ou em `rota` **e** `regra de negócio`) é
violação de camada por definição.

**Sinais de que "existe pasta mas não existe camada"** — comum em projeto parcialmente
organizado, e o caso mais fácil de passar batido:
- `services/` cujas classes nunca são instanciadas fora dela;
- helpers/validators/constantes definidos e nunca importados;
- método no model (ex.: `is_overdue()`) reimplementado inline nas rotas;
- ausência total de arquivos de controller enquanto os handlers de rota têm 50+ linhas.

Confirme sempre com busca de uso real:

```bash
grep -rn "NomeDaClasse\|nome_da_funcao" . --include='*.py' --include='*.js' | grep -v node_modules
```

## 7. Domínio da aplicação

Triangule três fontes: nomes de tabelas, prefixos de rota e dados de seed. Descreva em uma
linha, no vocabulário do negócio, não no do framework.
Ex.: `users + courses + enrollments + payments` + `/api/checkout` ⇒ "plataforma de cursos
(LMS) com fluxo de checkout e matrícula".

## 8. Métricas

```bash
# arquivos-fonte e linhas (ajuste as extensões à linguagem detectada)
find . -name '*.py' -o -name '*.js' -o -name '*.ts' | grep -vE "node_modules|\.venv|venv|dist|build|\.claude" | xargs wc -l | tail -1
```

Colete e guarde para o relatório: nº de arquivos-fonte, LOC, maior arquivo, maior função
(em linhas), profundidade máxima de aninhamento, nº de rotas.

**Exclua sempre da contagem:** dependências (`node_modules`, `.venv`, `site-packages`),
lockfiles, build/dist, migrations geradas, e os próprios arquivos da skill (`.claude/`).

## 9. Arquitetura atual — como resumir

Uma frase objetiva, com número: quantos arquivos, quais camadas existem de fato, e o que
falta. Sem adjetivo vazio ("código ruim") — só fato verificável.

- "Monolítica: 4 arquivos, nomes sugerem MVC mas `models.py` acumula SQL, regra e formatação;
  sem config, sem middleware, roteamento no entry point."
- "God Class: 1 classe (141 linhas) com DDL, rotas, pagamento e cache; `app.js` só faz bootstrap."
- "Parcialmente organizada: `models/`, `routes/`, `services/`, `utils/` existem, mas não há
  camada de controller — regra de negócio vive nas rotas e `services/` está morto."
