# Technology-Agnostic MVC Target

MVC is the required target for every project. Apply it by responsibility, not by requiring a specific framework, folder layout, or interface type. Preserve sound existing boundaries and adapt names to the technology.

## Universal MVC Mapping

- **Model:** owns domain state, rules, invariants, calculations, and access to state through appropriate abstractions. It must not depend on how users or systems interact with the application.
- **View:** presents Model/application results to an external consumer. A View can be a GUI component, API serializer/response, CLI formatter, event payload, report, file output, or another presentation adapter.
- **Controller:** receives an external action/input, validates or translates it, invokes the Model/application use case, and selects the resulting View/output.

Supporting components such as services, repositories, configuration, middleware, gateways, and composition roots are allowed when they clarify MVC responsibilities. They support MVC; they do not replace it.

## Boundaries

### Configuration

- Read environment variables and define safe local defaults.
- Validate required production settings at startup.
- Never expose secrets through health endpoints, logs, or serializers.

### Models And Entities

- Represent domain data, relationships, and local invariants.
- Avoid UI, HTTP, CLI, event, file-format, or other presentation concerns.
- Avoid orchestration across multiple domains or external integrations.

### Repositories And Data Access

- Own queries, persistence mapping, and database-specific behavior.
- Use parameterized queries or safe ORM predicates.
- Expose operations meaningful to the domain rather than raw cursors.

### Services

- Own business rules, use cases, transaction boundaries, and integration coordination.
- Accept dependencies through constructors/functions or a composition root.
- Return domain/application results, not framework responses.

### Controllers

- Coordinate one application flow.
- Receive actions from an interface and translate validated input into Model/service calls.
- Select the View or output path for the result without owning presentation details.
- Do not build SQL or implement core business rules.

### Views And Interface Adapters

- Present output for the project's real consumers.
- Keep formatting, serialization, rendering, protocol mapping, and interface-specific response behavior outside Models.
- Stay thin enough to understand the observable contract at a glance.

Examples:

| Interface | Controller input | View output |
|---|---|---|
| Web/API | route/request | template, serializer, response |
| Desktop/mobile UI | user action/event | rendered screen/view model |
| CLI | parsed command/options | formatted stdout/stderr and exit code |
| Event consumer | message/event | emitted event/acknowledgement |
| Batch/file flow | job/file trigger | report/output file/status |
| Library | public function/method call | stable return object/error contract |

### Error Handling

- Define typed/domain-specific errors.
- Map errors to each external interface centrally and consistently.
- Log internal details server-side and return safe client messages.

### Entry Point

- Act as composition root: load config, create dependencies, register routes/middleware, and start the server.
- Avoid business rules and interface-specific work.

## Suggested Structures

Adapt to project size. A small application can group by layer:

```text
src/
  config/
  models/
  repositories/
  services/
  controllers/
  routes/
  middleware/
  app
```

A larger application can group by domain while preserving the same MVC responsibilities:

```text
src/
  products/
    model
    repository
    service
    controller
    routes
  orders/
  shared/
    config
    database
    errors
  app
```

These layouts are examples, not requirements. Use conventions native to the detected language/framework when responsibilities remain clear.

## Dependency Direction

Views/interface adapters depend on controllers; controllers depend on Models/application services; Models remain independent of Views and Controllers. Persistence/integration adapters support Models/services and must not import presentation code.

## Compatibility Rules

- Preserve all observable contracts during structural extraction: routes, UI behavior, commands, event schemas, library APIs, files, statuses, and errors.
- Isolate necessary security-breaking changes and document them.
- Keep migrations explicit when schema changes are unavoidable.
- Prefer incremental extraction over a single rewrite.

## Validation Standard

A refactor is complete only when:

- imports/syntax pass;
- tests pass or missing coverage is stated;
- the application boots;
- every original observable contract has a smoke-test result;
- corrected security findings have regression checks;
- a fresh audit records remaining risks.
