# Guidelines da Arquitetura MVC Alvo (Fase 3)

Para APIs backend, a **View** é a camada de apresentação HTTP: rotas + serialização da resposta (JSON). O fluxo de dependências é **sempre unidirecional**:

```
HTTP ─▶ Views/Routes ─▶ Controllers ─▶ Models ─▶ Banco
                           │
                           └──▶ Services (integrações / side-effects)
Config ◀── todos leem configuração; ninguém lê variáveis de ambiente fora de config/
Middlewares ── envolvem a pipeline (erros, auth)
Composition root (app.py / app.js) ── cria e injeta tudo
```

Uma camada **nunca** importa a camada acima dela (Model não conhece Controller; Controller não conhece rota/Blueprint/Router).

## Estrutura alvo de referência

### Python / Flask
```
<projeto>/
├── app.py                      # shim: mantém `python app.py` funcionando (importa create_app)
├── src/                        # (ou na raiz, se o projeto já for organizado por pastas — ver "Adaptação")
│   ├── __init__.py
│   ├── app.py                  # composition root: create_app()
│   ├── config/settings.py      # configuração via os.environ com defaults seguros
│   ├── database/               # conexão (por request), schema e seed
│   ├── models/                 # um arquivo por entidade/agregado
│   ├── controllers/            # um arquivo por recurso/caso de uso
│   ├── views/                  # Blueprints: rotas → controller (ou routes/)
│   ├── services/               # notificação, pagamento, cache, tokens
│   ├── middlewares/            # error_handler.py, auth.py
│   └── utils/                  # helpers puros (sem estado, sem I/O)
├── .env.example
└── requirements.txt
```

### Node.js / Express
```
<projeto>/
├── src/
│   ├── app.js                  # composition root: createApp() + listen
│   ├── config/index.js         # process.env com defaults seguros
│   ├── database/               # conexão, wrapper async, schema/seed
│   ├── models/                 # repositórios por entidade
│   ├── controllers/            # fluxo de cada recurso/caso de uso
│   ├── views/ (ou routes/)     # express.Router(): rota → controller
│   ├── services/               # pagamento, cache, hashing
│   ├── middlewares/            # errorHandler.js, asyncHandler.js, auth.js
│   └── utils/
├── .env.example
└── package.json                # "start" continua funcionando
```

## Responsabilidades por camada

### Config (`config/`)
- **Única** origem de configuração: lê `os.environ` / `process.env` (pode usar `python-dotenv`/`dotenv` se já for dependência).
- Segredos **sem default real**: default vazio ou gerado em runtime (ex.: `secrets.token_hex(32)` para dev) + aviso no log.
- Flags seguras por padrão: `DEBUG=false`, `HOST=127.0.0.1` (ou o que o projeto exigir), porta configurável via `PORT`.
- Pode conter constantes de domínio? **Não** — essas ficam nos Models (ou `models/constants`).

### Models (`models/`)
- Representam entidades e encapsulam **acesso a dados** (queries parametrizadas, ORM) e **regras de domínio** intrínsecas (ex.: `Task.is_overdue()`, cálculo de desconto, transições de status válidas, constantes de domínio).
- Serializam a entidade para dicionário **sem campos sensíveis** (`to_dict()` nunca devolve senha).
- Não conhecem HTTP (`request`, `jsonify`, `res`, status codes).
- Não disparam notificações/e-mails (isso é Service, chamado pelo Controller).

### Controllers (`controllers/`)
- Concentram o **fluxo da aplicação** de cada caso de uso: validar entrada → chamar Models/Services → montar resultado.
- Recebem dados já extraídos (dict/objeto) e devolvem dados ou lançam **exceções de domínio** (`NotFoundError`, `ValidationError`, `ConflictError`). Não montam respostas HTTP.
- Recebem dependências pelo construtor (DI): `ProductController(product_model, notification_service)`.
- Sem SQL, sem cálculos de domínio pesados (delegar ao Model), sem `print`.

### Views / Routes (`views/` ou `routes/`)
- Mapeiam método + path → controller. Extraem `request.get_json(silent=True)`, `request.args`, path params.
- Serializam a resposta e definem o **status code** (`jsonify(...), 201`).
- Sem regra de negócio, sem acesso a banco, sem try/except genérico (o middleware trata).
- Mantêm **exatamente** os paths/métodos e o envelope de resposta originais (ex.: `{"dados": ..., "sucesso": true}`).

### Services (`services/`)
- Integrações e side-effects: envio de e-mail/SMS, gateway de pagamento, cache, geração de tokens, hashing.
- Stateless ou com estado encapsulado em instância injetada (nunca estado global de módulo).

### Middlewares (`middlewares/`)
- **Error handler centralizado**: converte exceções de domínio em JSON + status (400/401/403/404/409) e erros inesperados em 500 **genérico** (logando o stacktrace, sem vazar `str(e)`).
- Mantém o formato de erro já usado pela API (ex.: `{"erro": "...", "sucesso": false}` ou `{"error": "..."}`).
- Auth/admin guards quando há endpoints administrativos.

### Composition root (entry point)
- Cria a app (factory `create_app()` / `createApp()`), carrega config, inicializa banco, **instancia models → services → controllers** injetando dependências, registra views e middlewares.
- É o único lugar que "conhece" todas as implementações concretas.
- Mantém o comando de execução original (`python app.py`, `npm start`) — use um shim se mover o código para `src/`.

## Regras de dependência (verificáveis)

| Camada | Pode importar | Não pode importar |
|---|---|---|
| views/routes | controllers (via injeção), framework HTTP | models, database, SQL |
| controllers | models, services, exceptions, validators | framework HTTP (`request`, `jsonify`, `res`) |
| models | database, utils, constants | controllers, views, services, HTTP |
| services | config, utils | controllers, views |
| config | stdlib | qualquer camada |

Verificação rápida: `grep -rn "jsonify\|request\." controllers/` deve ser vazio; `grep -rn "execute(\|db.session\|SELECT" controllers/ views/` deve ser vazio.

## Adaptação ao contexto

| Situação encontrada | Estratégia |
|---|---|
| **Monolito em poucos arquivos** (tudo em `app.py`/`models.py`/`controllers.py`) | Criar `src/` com todas as camadas; deixar `app.py` raiz como shim; apagar os arquivos legados ao final. |
| **God Class** que cria banco e rotas (`AppManager`) | Desmontar a classe: schema/seed → `database/`; cada bloco de rota → controller + view; helpers → services. O entry point existente (ex.: `src/app.js`) vira composition root. |
| **Camadas parciais** (`models/`, `routes/`, `services/`, `utils/` na raiz) | **Não mover tudo para `src/`.** Manter as pastas existentes (`routes/` = camada View), adicionar `config/`, `controllers/`, `middlewares/`; esvaziar as rotas de regra de negócio; conectar services desconectados; usar/limpar `utils`. Preservar scripts que importam a app (ex.: `seed.py` → `from app import app, db`). |
| Projeto usa ORM | Models continuam sendo as classes ORM; adicionar métodos de consulta/regra nelas ou em repositórios finos. |
| SQL cru | Models como módulos/classes de repositório com SQL parametrizado; conexão por request. |

## Contrato HTTP — o que preservar

- Paths, métodos, nomes de parâmetros (inclusive nomes ruins de payload como `usr`, `eml` — renomeie só internamente).
- Status codes de sucesso e de erro conhecidos.
- Envelope e chaves de resposta.

Mudanças permitidas **apenas por segurança** (documente no resumo da Fase 3):
- Remover campos sensíveis das respostas (`senha`, `password`, `secret_key`).
- Exigir credencial em endpoints administrativos/destrutivos.
- Substituir mensagens de erro internas (`str(e)`) por mensagens genéricas.
- Recusar entradas que antes geravam comportamento inseguro (ex.: senha padrão implícita).
