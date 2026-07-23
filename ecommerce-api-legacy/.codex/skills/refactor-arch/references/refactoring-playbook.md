# Playbook agnóstico de refatoração

Selecione transformações pelos findings aprovados; não execute esta lista como receita fixa. Os exemplos usam pseudocódigo intencionalmente neutro. Traduza-os para as construções, lifecycle, tipos e convenções descobertas na codebase.

## Sumário

1. [T01 — Extrair configuração e segredos](#t01--extrair-configuração-e-segredos)
2. [T02 — Tornar operações dinâmicas seguras](#t02--tornar-operações-dinâmicas-seguras)
3. [T03 — Afinar uma View ou adapter](#t03--afinar-uma-view-ou-adapter)
4. [T04 — Dividir um God component](#t04--dividir-um-god-component)
5. [T05 — Substituir estado global por dependência explícita](#t05--substituir-estado-global-por-dependência-explícita)
6. [T06 — Criar fronteira transacional](#t06--criar-fronteira-transacional)
7. [T07 — Eliminar acesso N+1](#t07--eliminar-acesso-n1)
8. [T08 — Centralizar validação e apresentação](#t08--centralizar-validação-e-apresentação)
9. [T09 — Proteger credenciais e DTOs públicos](#t09--proteger-credenciais-e-dtos-públicos)
10. [T10 — Centralizar tratamento de erros](#t10--centralizar-tratamento-de-erros)
11. [T11 — Modernizar API deprecated](#t11--modernizar-api-deprecated)

## T01 — Extrair configuração e segredos

**Aplica a:** AP-02, AP-13.

**Antes**

```text
application.secret = "literal-secret"
application.debug = true
host.start(port = 5000)
```

**Depois**

```text
settings = Configuration.load(external_sources)
settings.require("APPLICATION_SECRET")

application = ApplicationFactory.create(settings)
host.start(application, settings.port, settings.debug)
```

**Passos:** inventarie configuração; redija segredos; use o mecanismo externo seguro do ecossistema; valide campos no bootstrap; injete settings; documente somente chaves necessárias. Trate rotação de credencial como ação externa separada.

**Verifique:** valor obrigatório ausente falha claramente; testes injetam configuração falsa; nenhum segredo aparece em fonte, diff, log, relatório ou contrato público.

## T02 — Tornar operações dinâmicas seguras

**Aplica a:** AP-01.

**Antes**

```text
statement = "SELECT item WHERE id = " + external_input.id
data_store.execute(statement)

process.execute("tool " + external_input.argument)
```

**Depois**

```text
data_store.execute("SELECT item WHERE id = :id", parameters = { id: external_input.id })

allowed_argument = AllowedArguments.parse(external_input.argument)
process.execute(executable = "tool", arguments = [allowed_argument], shell = false)
```

**Passos:** trace origem até sink; use binding/AST/API estruturada; aplique allowlist a identificadores que não aceitam parâmetros; elimine executor genérico exposto externamente.

**Verifique:** payloads de escape são tratados como dados; autorização restringe operações; nenhuma concatenação de entrada alcança interpretador, query engine, template engine ou shell.

## T03 — Afinar uma View ou adapter

**Aplica a:** AP-04, AP-05, AP-09.

**Antes**

```text
on_external_request(input):
    validate_business_rules(input)
    record = data_store.query(input.id)
    result = calculate(record, input)
    external_service.send(result)
    return protocol_response(result)
```

**Depois**

```text
on_external_request(raw_input):
    command = InputAdapter.to_command(raw_input)
    result = controller.execute(command)
    return OutputAdapter.present(result)

controller.execute(command):
    validated = policy.validate(command)
    entity = repository.load(validated.id)
    result = domain_service.apply(entity, validated)
    notifier.notify(result)
    return result
```

**Passos:** congele contrato; extraia parser/formatter; mova orquestração; injete fronteiras externas; mantenha o adapter limitado ao protocolo.

**Verifique:** identidade, entrada, saída e erros permanecem; Controller testa sem host/protocolo; adapter não importa driver de dados nem SDK de integração.

## T04 — Dividir um God component

**Aplica a:** AP-04, AP-05, AP-12.

**Antes**

```text
class SystemManager:
    initialize_schema()
    seed_data()
    register_interfaces()
    validate_orders()
    charge_customers()
    create_reports()
    format_outputs()
```

**Depois**

```text
bootstrap:
    repositories = build_repositories(data_store)
    payment_port = build_payment_adapter(configuration)
    order_use_case = OrderUseCase(repositories, payment_port)
    report_use_case = ReportUseCase(repositories)
    adapters = build_input_adapters(order_use_case, report_use_case)
    return build_host(adapters)
```

**Passos:** agrupe responsabilidades por motivo de mudança e domínio; extraia primeiro fronteiras de infraestrutura; mova um contrato por vez; mantenha composition root único; remova o componente antigo após equivalência.

**Verifique:** cada módulo tem responsabilidade principal; casos de uso usam doubles; bootstrap compõe sem lógica de domínio.

## T05 — Substituir estado global por dependência explícita

**Aplica a:** AP-06.

**Antes**

```text
global connection = null

get_connection():
    if connection is null:
        connection = open_connection(fixed_configuration)
    return connection
```

**Depois**

```text
bootstrap(configuration):
    connection_factory = ConnectionFactory(configuration.data_store)
    register_scope(
        create = connection_factory.open,
        dispose = connection.close
    )

controller(repository_factory):
    repository = repository_factory.for_current_scope()
```

Use o lifecycle nativo detectado. Um recurso comprovadamente thread-safe pode ter escopo de processo; uma sessão/transação mutável geralmente exige escopo por operação.

**Verifique:** testes injetam recurso temporário; recursos encerram no lifecycle; operações concorrentes não compartilham transação ou estado acidentalmente.

## T06 — Criar fronteira transacional

**Aplica a:** AP-07.

**Antes**

```text
enrollment = enrollment_store.insert(data)
payment_store.insert(enrollment.id, amount)
audit_store.insert("completed", enrollment.id)
```

**Depois**

```text
unit_of_work.run(transaction):
    enrollment = enrollment_store.insert(data, transaction)
    payment_store.insert(enrollment.id, amount, transaction)
    outbox_store.add(Event("completed", enrollment.id), transaction)
```

Efeito externo fora do mesmo mecanismo transacional exige idempotência, outbox, saga ou compensação; não finja atomicidade impossível.

**Passos:** defina unidade de consistência; mova commit/rollback ao caso de uso; passe contexto aos stores; modele falha externa.

**Verifique:** falha no segundo/terceiro passo não deixa estado parcial; retry não duplica efeito; falso sucesso nunca é publicado.

## T07 — Eliminar acesso N+1

**Aplica a:** AP-08.

**Antes**

```text
orders = order_store.list()
for order in orders:
    order.customer = customer_store.get(order.customer_id)
    order.items = item_store.list_by_order(order.id)
```

**Depois**

```text
orders = order_store.list_with_related_data()

# implementação adequada ao store detectado:
# join/eager-load, batch by identifiers, graph fetch ou bulk request
```

**Passos:** meça acessos; escolha join, eager loading ou lote conforme cardinalidade; preserve ordenação, paginação e shape; evite carregar grafo desnecessário.

**Verifique:** número de acessos permanece constante ou cresce em lotes; volume de dados é controlado; contrato continua equivalente.

## T08 — Centralizar validação e apresentação

**Aplica a:** AP-09, AP-13.

**Antes**

```text
adapter_A:
    if status not in [PENDING, DONE]: return protocol_error
    return { id, title, status }

adapter_B:
    if status not in [PENDING, DONE]: return another_error
    return { id, title, status, internal_field }
```

**Depois**

```text
UpdatePolicy.validate(input):
    if input.status not in ALLOWED_STATUS:
        raise ValidationError("invalid status")
    return UpdateCommand(input.status)

PublicPresenter.present(entity):
    return PublicDTO(entity.id, entity.title, entity.status)
```

**Passos:** confirme duplicação semântica; extraia policy/validator independente de protocolo; centralize DTO público; preserve divergências intencionais documentadas.

**Verifique:** interfaces equivalentes aplicam mesmas regras; campos sensíveis não escapam; erros mantêm contrato aprovado.

## T09 — Proteger credenciais e DTOs públicos

**Aplica a:** AP-02, AP-03.

**Antes**

```text
user.password = fast_or_reversible_transform(raw_password)

user.to_public_data():
    return { id, email, password }
```

**Depois**

```text
user.password_hash = adaptive_password_hasher.hash(raw_password)

user.verify_password(candidate):
    return adaptive_password_hasher.verify(user.password_hash, candidate)

PublicUserPresenter.present(user):
    return { id, email, role }
```

**Passos:** escolha biblioteca segura suportada pelo ecossistema; remova defaults; planeje migração/rehash; use allowlist em DTOs; aplique autenticação e autorização na fronteira.

**Verifique:** hash usa salt e custo adaptativo; segredo/hash não aparece externamente; credenciais válidas/inválidas e permissões têm testes.

## T10 — Centralizar tratamento de erros

**Aplica a:** AP-10, AP-12, AP-14.

**Antes**

```text
adapter.handle(input):
    try:
        data_store.delete(input.id)
    catch any_error:
        log(raw_error)
    return success("removed")
```

**Depois**

```text
controller.remove(command):
    repository.remove(command.id) or raise NotFound

boundary_error_handler(error, context):
    mapped = ErrorMapper.to_public_contract(error)
    structured_logger.record(error, context.without_secrets)
    return mapped
```

**Passos:** modele erros; não silencie falhas; faça rollback/compensação; traduza apenas na fronteira; redija logs; mantenha códigos/envelopes/tipos aprovados.

**Verifique:** falha nunca retorna sucesso; detalhe interno não vaza; logs têm contexto; contratos de erro são consistentes.

## T11 — Modernizar API deprecated

**Aplica a:** AP-11.

Execute somente quando símbolo, versão efetiva, fonte primária e substituto estiverem confirmados.

**Antes**

```text
result = LegacyApi.old_operation(input)
timestamp = LegacyClock.naive_now()
```

**Depois**

```text
result = SupportedApi.replacement_operation(input, explicit_options)
timestamp = Clock.current_time(explicit_timezone)
```

**Passos:** fixe versão de runtime/dependência; leia migration guide oficial; identifique mudança de retorno, erro, timezone, lifecycle ou concorrência; atualize um uso por vez; separe upgrade de dependência quando aumentar risco.

**Verifique:** warning desaparece; testes cobrem diferenças semânticas; build e execução usam a versão declarada/resolvida. Não use substituição textual global sem revisão.

## Matriz de seleção e ordem

| Finding | Transformações prováveis | Ordem heurística |
|---|---|---:|
| AP-01 | T02 | 1 |
| AP-02 | T01, T09 | 1 |
| AP-03 | T09 | 1 |
| AP-04 | T03, T04 | 3–4 |
| AP-05 | T03, T04, T08 | 3–4 |
| AP-06 | T05 | 2 |
| AP-07 | T06 | 3 |
| AP-08 | T07 | 3 |
| AP-09 | T08 | 3 |
| AP-10 | T10 | 4 |
| AP-11 | T11 | após testes de caracterização |
| AP-12 | T04, T06, T10 | 3–4 |
| AP-13 | T01, T08 | 1–3 |
| AP-14 | T08, T10 ou limpeza localizada | por último |

Trate primeiro vulnerabilidades e seams de configuração, depois lifecycle/dados, papéis MVC e acabamento. Após cada transformação, execute a validação mais próxima e confira o escopo antes de continuar.
