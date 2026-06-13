# Project Analysis Heuristics

## Purpose

Build an evidence-based map of an unfamiliar application before auditing or changing it.

## Inventory Order

1. Read top-level README and dependency manifests.
2. List files while excluding generated directories.
3. Prefer an exploratory subagent first when available; use the script only as a fallback helper.
4. Identify entry points and startup commands.
5. Identify every external interface: UI, HTTP/RPC, CLI, events, jobs, library API, files, devices, or other adapters.
6. Trace representative inputs inward through decisions and state changes, then outward to observable outputs.
7. Identify domain objects, state stores, integrations, generated code, tests, and operational tooling.

Exclude `.git`, `.venv`, `venv`, `node_modules`, `dist`, `build`, `coverage`, caches, generated clients, and vendor directories from source counts.

## Language And Dependency Detection

| Evidence | Likely language/tool |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python |
| `package.json`, lockfiles | JavaScript/TypeScript |
| `pom.xml`, `build.gradle*` | Java |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.sln`, `*.csproj`, `global.json` | .NET/C# |
| `Package.swift`, `*.xcodeproj` | Swift |
| `pubspec.yaml` | Dart/Flutter |
| `mix.exs` | Elixir |
| `project.clj`, `deps.edn` | Clojure |
| `CMakeLists.txt`, `Makefile`, `meson.build` | Native/mixed build |
| `*.tf` | Terraform |
| `Dockerfile`, compose files, CI files | Runtime/operations evidence |

This table is illustrative. Unknown manifests and extensions are evidence to investigate, not files to ignore. Confirm using source extensions, imports, build commands, generated metadata, and runtime entry points. Report mixed-language projects when more than one language contains application logic.

## Framework Detection

Use at least two signals when possible:

- Flask: dependency plus `Flask(...)`, `Blueprint`, or route decorators.
- Django: dependency plus `manage.py`, settings, or URL configuration.
- FastAPI: dependency plus `FastAPI(...)` or router decorators.
- Express: dependency plus `express()` or route registration.
- NestJS: dependency plus module/controller decorators.
- Spring: dependency plus application/controller annotations.
- Rails: Gemfile plus routes/application structure.

The list is not exhaustive. For an unknown framework, derive its role from imports, dependency metadata, annotations/macros, directory conventions, startup code, and official/local documentation. Do not infer a framework from a dependency that is unused.

## Unknown Technology Fallback

When no known detector matches:

1. List unknown extensions, manifests, build files, lockfiles, and executable/shebang files.
2. Inspect dependency names and imports/includes.
3. Read build, run, test, and deployment commands.
4. Locate generated-code headers and separate generated files from maintained source.
5. Inspect a representative entry point and test.
6. Use project-local documentation first; consult official technology documentation when available and necessary.
7. Record the technology as `custom` or `unknown` until evidence supports a precise name.

Never treat absence from a built-in table or script as absence from the project.

## State And Persistence Detection

Check dependencies, connection setup, migrations, schemas, models, query syntax, files, caches, queues, remote APIs, browser/device storage, and environment variables.

Classify every state mechanism:

- raw SQL;
- query builder;
- ORM;
- document/key-value/graph store;
- files or object storage;
- cache/session;
- queue/event log;
- remote service;
- in-memory/process state;
- no persistence;
- mixed.

Record lifecycle, ownership, consistency guarantees, transaction/atomicity boundaries, cleanup, and concurrency assumptions.

## Architecture Mapping

Trace representative flows from each interface through state/domain decisions to output. Then classify the current architecture and the degree of MVC separation:

- **Monolithic:** transport, business rules, and persistence live together.
- **Layered but coupled:** folders exist, but responsibilities cross boundaries.
- **MVC-like:** routes/views, controllers, and models are distinct.
- **Component/domain organized:** responsibilities are grouped by feature or bounded context.
- **Other:** describe the actual pattern without forcing it into a known label.

Folders alone are not proof of architecture. Inspect imports and responsibilities.

## MVC Role Mapping

Map responsibilities conceptually before proposing folders:

- **Model candidates:** domain state, rules, persistence abstractions, calculations, and invariants.
- **View candidates:** anything presenting output or adapting it for an external consumer, including UI, API response, CLI output, event payload, report, or file.
- **Controller candidates:** anything receiving an action/input and coordinating the Model and selected View.

A project may have multiple View and Controller adapter types. Technology-specific names do not need to contain `model`, `view`, or `controller`.

## Domain Detection

Infer the domain from:

1. public commands, screens, routes, events, exports, and actions;
2. entity/model/schema names;
3. README, examples, and tests;
4. business rules and external integrations.

Use a concise description such as `E-commerce API for products, users, orders, and sales reports`. Label weak conclusions as inferred.

## Source Count

Count only human-maintained application, test, migration, and configuration source files. State the included extensions or categories. Do not count dependencies, databases, lockfiles, generated assets, or virtual environments. Built-in inventory counts only recognized extensions; inspect unrecognized files before reporting the final count.

## Validation Discovery

Find:

- documented startup command;
- build/package/framework commands;
- tests and test runner;
- contract examples and fixtures;
- health/readiness checks when applicable;
- required environment variables;
- runtime lifecycle, ports, input files, services, and initialization behavior.

If tests do not exist, derive smoke checks from the observable contracts found in the project.
