# Guidelines da Arquitetura Alvo (MVC em Camadas)

Estrutura para a qual a Fase 3 converge, em qualquer linguagem. O que é fixo são as
**responsabilidades e as regras de dependência**; os nomes de arquivo seguem a convenção do
ecossistema detectado.

## Responsabilidade de cada camada

| Camada | Faz | Não faz |
|---|---|---|
| **Config** | Lê variáveis de ambiente, aplica defaults, valida presença de segredo obrigatório, expõe objeto de configuração por ambiente | Não contém valor secreto literal, não conhece HTTP nem domínio |
| **Model / Repository** | Estrutura da entidade, persistência (queries parametrizadas ou ORM), invariantes do agregado (`is_overdue()`, `has_stock()`), transação do próprio agregado | Não conhece request/response, não retorna código HTTP, não formata mensagem de erro de API |
| **Service** (só quando necessário) | Regra que atravessa agregados (checkout = curso + matrícula + pagamento + auditoria), integração externa (e-mail, gateway), transação que abrange vários models | Não conhece request/response |
| **Controller** | Recebe dados já extraídos da request, valida entrada, orquestra model/service, decide status e forma da resposta | Não escreve SQL, não implementa regra de domínio, não registra rota |
| **View / Routes** | Mapeia `método + caminho → controller`, declara middleware da rota, extrai parâmetros | Nenhuma lógica: sem `if` de negócio, sem acesso a dados |
| **Middleware** | Erro centralizado, autenticação/autorização, log de request, CORS, validação de schema | Não contém regra de domínio |
| **Entry point / Composition root** | Cria a aplicação, carrega config, instancia dependências e injeta, registra rotas e middlewares, sobe o servidor | Não define rota inline, não contém regra nem segredo |

## Regra de dependência (não negociável)

```
routes → controllers → services → models → (driver de banco)
                    ↘ models
config → (lido por todos)     middlewares → (transversal)
```

- A seta é de mão única. **Model nunca importa controller; controller nunca importa rota.**
- Camada de fora conhece a de dentro, nunca o contrário.
- Nada de import circular. Se aparecer, a responsabilidade está no lugar errado.
- Dependência entra por parâmetro/construtor (injeção), não por import de singleton mutável.

## Estrutura por stack

### Python / Flask
```
src/
├── config/settings.py          # classes Config/DevConfig/ProdConfig lendo os.environ
├── models/<agregado>_model.py  # persistência + invariantes por agregado
├── controllers/<agregado>_controller.py
├── services/<nome>_service.py  # só se houver regra multi-agregado
├── views/routes.py             # blueprints: caminho → controller
├── middlewares/error_handler.py
├── utils/                      # funções puras
└── app.py                      # create_app(): factory + composition root
run.py                          # ponto de entrada do servidor
.env.example
```
Notas: um blueprint por agregado, registrado no factory. `create_app(config)` recebe a config
para permitir ambiente de teste. Nada de `db.create_all()` em tempo de import — chame dentro
do factory sob `app_context()` ou em script de inicialização.

### Node.js / Express
```
src/
├── config/index.js             # process.env + validação de obrigatórios
├── models/<agregado>.repository.js
├── controllers/<agregado>.controller.js
├── services/<nome>.service.js
├── routes/index.js             # + <agregado>.routes.js
├── middlewares/{errorHandler,auth}.js
├── database/{connection.js,schema.sql}
├── utils/
└── app.js                      # cria express, injeta deps, registra rotas
server.js                       # listen()
.env.example
```
Notas: `app.js` exporta o app sem escutar porta (permite teste); `server.js` chama `listen`.
Error middleware é registrado **por último**. Em base com API de callback, promisifique o
driver na camada de repository e use `async/await` acima dela.

### Outras stacks
Mantenha as mesmas camadas na convenção nativa: Django (`models.py`/`views.py` como
controller/`urls.py`/`services.py`), Spring (`@Repository`/`@Service`/`@RestController`),
Laravel (`app/Models`, `app/Http/Controllers`, `routes/`), NestJS (module/controller/service/
repository — já é MVC por construção; nesse caso a refatoração é redistribuir responsabilidade,
não criar pastas).

## Granularidade correta

- **Um model e um controller por agregado de domínio** (produto, usuário, pedido), derivados do
  domínio real levantado na Fase 1 — **não** um por arquivo legado existente.
- Não crie camada vazia por simetria: se não há regra multi-agregado, não crie `services/`.
  Camada fantasma é anti-pattern (AP-13), não organização.
- Relatórios/consultas analíticas: controller próprio (`report_controller`) que consulta
  models — não espalhe agregação pelas rotas.
- Arquivo legado que sobrou vazio depois da migração é removido, não deixado como stub.

## Checklist de conformidade da Fase 3

- [ ] Diretórios refletem as camadas; cada arquivo tem uma responsabilidade declarável em uma frase
- [ ] Zero segredo literal no código; tudo por variável de ambiente, com `.env.example` e `.env` no `.gitignore`
- [ ] Models isolam persistência: nenhuma query fora deles (`grep` por SQL/ORM fora de `models/` volta vazio)
- [ ] Nenhum `import` de framework HTTP dentro de `models/` ou `services/`
- [ ] Controllers sem SQL e sem regra de domínio duplicada
- [ ] Routes sem lógica — só mapeamento e middleware
- [ ] Tratamento de erro centralizado em middleware; handlers sem `try/except` repetido por endpoint
- [ ] Toda escrita multi-tabela dentro de uma transação com rollback
- [ ] Entry point é composition root: config + injeção + registro, sem rota inline
- [ ] Log estruturado por logger configurável, sem `print`/`console.log` de diagnóstico
- [ ] Mesmas rotas e mesmos códigos de status de antes (exceto mudança de segurança declarada)
- [ ] Sem import circular; regra de dependência respeitada nos dois sentidos
