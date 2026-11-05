# 04 — Guidelines de arquitetura (MVC alvo)

Use na **Fase 3** para planejar a estrutura-alvo e para decidir *o que criar, mover ou só corrigir*. Definimos **papéis**, não pastas: a convenção idiomática do framework detectado vence qualquer layout deste arquivo.

## 1. Papéis e responsabilidades

| Papel | Responsabilidade | Pode depender de | Proibido |
|---|---|---|---|
| **Config** | Ler ambiente/arquivos e expor configuração tipada (porta, banco, segredos, flags). Valores sensíveis vêm do ambiente; nenhum segredo literal | — | Lógica de negócio, acesso a dados |
| **Model** (dados) | Entidades, acesso a dados (queries parametrizadas/ORM), integridade e constraints, mapeamento linha↔objeto | Config | HTTP (request/response), formatação de resposta, regras de apresentação |
| **Service** (opcional, recomendado quando há regra) | Regra de negócio reutilizável, cálculo, orquestração de models, transações | Models, Config | HTTP, SQL cru |
| **Controller** | Receber a entrada já roteada, validar formato, chamar service/model, escolher status e dados de retorno | Services, Models | SQL, regra de negócio pesada, detalhes de infraestrutura |
| **View / Routes** | Mapear método+caminho → controller; **serialização de saída** (DTO sem campos sensíveis); registrar middlewares por rota | Controllers | Regra de negócio, acesso a dados |
| **Middleware** | Autenticação/autorização, tratamento central de erros, rate limit, CORS, cabeçalhos de segurança, logging | Config | Regra de domínio |
| **Composition root** (entry point) | Único lugar que cria dependências (conexão, repositórios, serviços), registra rotas/middlewares e inicia o servidor | Todos | Lógica de negócio |

Em APIs JSON, "View" = camada de rotas + serializadores (não há template HTML).

## 2. Regras de dependência (sentido único)

```
Entry point → Routes/View → Controller → Service → Model → (banco)
                  ↑ Middleware           ↘ Config (lida por todos, injetada)
```

- Camadas superiores dependem das inferiores; **nunca o contrário** (model não importa controller; service não importa framework web).
- Infraestrutura (conexão, cliente HTTP, relógio) é **criada no composition root e injetada**; módulos não instanciam infraestrutura sozinhos (ARC-04).
- Estado mutável não fica em variável global de módulo (ARC-03): vive em objeto criado no composition root ou na camada de dados.
- Um módulo = um papel e, quando possível, um domínio (ARC-01, ARC-06).

## 3. Estrutura-alvo de referência (adapte; não imponha)

Genérica:
```
src/ (ou raiz do app)
├── config/            # settings e leitura de ambiente
├── models/            # entidades e acesso a dados, por domínio
├── services/          # regra de negócio (quando houver)
├── controllers/       # um por domínio
├── routes/ (views/)   # registro de rotas + serializadores
├── middlewares/       # auth, error handler, rate limit
└── app.<ext>          # composition root (+ server entry se separado)
```

Mapeamento por framework (siga a convenção nativa quando existir):

| Stack | Como mapear |
|---|---|
| Flask | app factory `create_app()`; blueprints por domínio = routes; `controllers/` com funções/classes; models (SQLAlchemy ou camada de dados); `errorhandler` global; config por classe/objeto lido do ambiente |
| FastAPI | `routers/` (routes), `schemas/` (serialização/validação), `services/`, `repositories/`/models; `Depends` para injeção; handlers de exceção |
| Django | já é MVT: respeite `models.py`, `views.py`/`viewsets`, `urls.py`, `serializers`; mova regra para `services.py`; settings por ambiente |
| Express/Koa/Fastify | `routes/` (routers), `controllers/`, `services/`, `models/`, `middlewares/`, `config/`; `app.js` monta e exporta a app, `server.js` escuta a porta |
| NestJS | módulos por domínio, controllers, providers (services), DTOs, guards, filters (já é o padrão) |
| Spring Boot | `controller` / `service` / `repository` / `model` / `config` / `exception`; `@ControllerAdvice` para erros |
| Rails | MVC nativo; regra em models/services; `rescue_from` para erros |
| Laravel | rotas, controllers, models Eloquent, services, middleware, `Handler` de exceções |
| Go (Gin/Echo/chi) | pacotes `handler`, `service`, `repository`, `config`, `middleware`; construção em `main` |
| ASP.NET Core | controllers, services, repositories, middleware, `appsettings` + options pattern |
| Outro/desconhecido | aplique os papéis da seção 1 com a convenção de nomes da linguagem; registre em Observações que a estrutura foi derivada |

## 4. Adaptação ao nível de organização (rótulo da Fase 1)

| Rótulo | O que fazer |
|---|---|
| `monolito-sem-camadas` | Criar todas as camadas necessárias; dividir por domínio; mover config, dados, regra, rotas e erros para seus papéis; criar o composition root |
| `parcialmente-em-camadas` | **Não recriar** o que já está certo. Mover só o que está no papel errado (regra do handler → service; SQL da rota → model; CRUD no módulo de outro domínio → seu módulo), ativar serviços não usados ou removê-los, centralizar erros/config, remover código morto, corrigir o composition root |
| `em-camadas` | Corrigir apenas desvios reportados; Fase 3 mínima |

Princípio: **a menor mudança estrutural que elimine os findings aprovados.** Mantenha nomes e convenções já usados no projeto quando coerentes.

## 5. Regras por camada (para a refatoração)

- **Config:** um módulo único; segredos só via ambiente; falhar de forma clara se um segredo obrigatório faltar em produção; fornecer `.env.example` (sem valores reais) quando o projeto usa variáveis de ambiente; nunca criar/alterar `.env` real nem commitar segredos.
- **Models:** consultas **sempre parametrizadas**; um arquivo por domínio; funções devolvem entidades/dicts internos (a serialização pública é da view); constraints (`UNIQUE`, `NOT NULL`, FK) declaradas; sem `SELECT *` em listagens públicas.
- **Services:** funções puras quando possível; recebem dependências por parâmetro/construtor; transações aqui ou no model, nunca no controller.
- **Controllers:** validam formato (P-07), chamam service/model, traduzem exceções de domínio para status; sem SQL.
- **Routes/Views:** só mapeamento e serialização; **DTO** de saída sem senha/hash/segredo/config interna (P-04); rotas administrativas atrás de autenticação/perfil ou desativadas por flag (P-05).
- **Middlewares:** erro central (formato único de resposta, sem `str(e)` ao cliente, log do detalhe); autenticação; limites; cabeçalhos.
- **Composition root:** cria conexão/repositórios/serviços e injeta; é onde `debug`/host/porta são lidos da config (nunca fixos).

## 6. Checklist verificável de estrutura (alimenta a Fase 3 do checklist de validação)

Cada item é verificável por inspeção/busca; registre o resultado no relatório com arquivo:linha.

| Item do checklist | Critério objetivo |
|---|---|
| Estrutura de diretórios segue padrão MVC | Existem módulos distintos para config, models/dados, controllers, routes/views e entry point; nenhum arquivo concentra ≥ 3 papéis |
| Configuração extraída (sem hardcoded) | Busca por segredos/flags fixos (SEC-02, SEC-05) não retorna ocorrências fora de exemplos/testes |
| Models abstraem dados | Nenhuma consulta fora de `models`/camada de dados; todas parametrizadas |
| Views/Routes separadas | Arquivos de rotas contêm apenas mapeamento/serialização |
| Controllers concentram o fluxo | Handlers chamam services/models; sem SQL, sem regra pesada |
| Error handling centralizado | Existe handler global; nenhum `str(e)`/stack para o cliente; sem `except:` nu |
| Entry point claro | Um arquivo cria a app, registra rotas/middlewares e inicia; comando de execução documentado |

## 7. Preservação de comportamento

- O **contrato público** (rotas, métodos, formato e chaves de resposta, status) permanece, exceto mudanças aprovadas (`CT-xx`).
- Mantenha a forma dos envelopes de resposta existentes (ex.: `{"dados":..., "sucesso":...}`) ao mover código.
- Nomes de tabelas/colunas e formato de dados persistidos não mudam sem aprovação explícita (migração é classe D).
- Mudança de arquitetura não deve alterar a ordem de campos/semântica observável por clientes.
