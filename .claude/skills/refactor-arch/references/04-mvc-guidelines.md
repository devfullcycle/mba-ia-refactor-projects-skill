# Guidelines de Arquitetura — Padrão MVC Alvo

Estas são as regras do padrão MVC que a auditoria (Fase 2) usa para medir aderência e que a
refatoração (Fase 3) usa como destino. As **camadas conceituais são sempre as mesmas**; o
**layout de arquivos adapta-se à convenção da linguagem** (agnosticidade).

## As camadas e suas responsabilidades

### Model (camada de dados + regra de domínio)
- Representa e persiste as entidades do domínio; encapsula o **acesso a dados**.
- Contém a **regra de negócio** ligada à entidade.
- **Não** conhece HTTP (request/response), rotas nem formatação de saída.
- Toda query/SQL/ORM vive aqui (ou num repositório usado pelo model). Nada de SQL solto em rotas.

### View / Routes (camada de apresentação / roteamento)
- Em APIs, a "View" é a **camada de rotas**: mapeia caminho + método HTTP → um controller.
- Apenas **declara** as rotas e delega. **Não** contém regra de negócio nem acesso a dados.
- Responsável por serializar a resposta no formato do contrato (JSON), sem lógica de domínio.

### Controller (orquestração)
- Recebe a requisição já roteada, **valida a entrada**, chama os models/services necessários,
  monta a resposta e trata erros.
- É **magro**: orquestra, não implementa a regra de negócio (essa é do model/service).
- Um controller por recurso/domínio (ex.: `produto_controller`, `pedido_controller`).

### Config (configuração)
- Centraliza configuração e **segredos via ambiente** (nunca hardcoded): chaves, URLs de banco,
  flags de debug, portas.
- Um único ponto de verdade para configuração da aplicação.

### Middlewares (transversais)
- Preocupações transversais: **tratamento de erro centralizado**, CORS, autenticação, logging.
- Evita `try/except` repetido em cada rota.

### Entry point / Composition root
- Um arquivo fino que **monta a aplicação**: cria o app, carrega config, registra middlewares e
  rotas, injeta dependências (ex.: conexão de banco) e sobe o servidor.
- É onde as peças são conectadas — não contém regra de negócio.

## Fluxo alvo

```
Request → Route (view) → Controller → Model/Service → (DB)
                              ↓
Response ← Route (view) ← Controller ← Model/Service
        (erros → Middleware de erro centralizado)
```

## Layout por stack (mesmas camadas, idioma diferente)

**Python / Flask:**
```
src/
├── config/settings.py          # config + segredos via os.environ
├── models/<entidade>_model.py  # dados + regra por domínio
├── views/routes.py             # blueprints / mapeamento de rotas
├── controllers/<dominio>_controller.py
├── middlewares/error_handler.py
└── app.py                      # composition root (create_app)
```

**Node.js / Express:**
```
src/
├── config/index.js             # config + segredos via process.env
├── models/<entidade>.js        # ou repositories/ para acesso a dados
├── routes/<recurso>.routes.js  # mapeamento de rotas (a "view")
├── controllers/<recurso>.controller.js
├── middlewares/errorHandler.js
└── app.js                      # composition root
```

Para outras stacks, siga o idioma da linguagem mantendo as 6 camadas. Se o framework usa outra
convenção consagrada (ex.: services/repositories), respeite-a desde que a separação de
responsabilidades acima seja preservada.

## Como pontuar a aderência a MVC (Fase 2)

Avalie cada camada e atribua o checklist + um score de 0 a 10:

| Camada | `presente` | `parcial` | `ausente` |
|---|---|---|---|
| Models | acesso a dados e regra isolados por entidade | existe, mas com lógica vazando p/ rotas | SQL/regra espalhados, sem model |
| Views/Routes | rotas só mapeiam e delegam | rotas existem mas contêm lógica | rotas e handlers misturados no entrypoint |
| Controllers | controllers magros orquestrando | lógica parcial em controllers | não há camada de controller |
| Separation | camadas não se contaminam | alguma contaminação | God Class / tudo junto |

Rótulo do score: `Monolítico` (0–3), `Parcial` (4–7), `Aderente` (8–10). Baseie o número na
quantidade de camadas presentes e na ausência de contaminação. Justifique cada linha com um motivo
curto e concreto (o "porquê" observado no código).

## Anti-aderências comuns (viram findings de MVC)

- Regra de negócio dentro da rota/handler → mover para model/service (AP-06).
- SQL dentro de controller ou rota → mover para model/repositório.
- Estado global de conexão → injetar dependência no composition root (AP-05).
- Roteamento + lógica + dados no mesmo arquivo → separar em camadas (AP-01).
- Config/segredo hardcoded → extrair para `config` via ambiente (AP-02).
- Tratamento de erro repetido em cada rota → middleware centralizado.

Cada uma dessas, quando encontrada, entra como **finding** com arquivo e linhas exatas, além de
rebaixar o score de aderência.
